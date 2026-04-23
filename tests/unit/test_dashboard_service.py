"""Unit tests for dashboard_service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import backend.services.dashboard_service as dashboard_module
from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.bank import BankTransaction
from backend.models.cash import CashMovementType, CashRegister
from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.services.dashboard_service import (
    _month_start,
    _next_month,
    _shift_month,
    get_dashboard,
    get_monthly_chart,
    get_resources_chart,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_fy(
    db: AsyncSession,
    *,
    name: str = "2024",
    start: date = date(2024, 1, 1),
    end: date = date(2024, 12, 31),
    status: FiscalYearStatus = FiscalYearStatus.OPEN,
) -> FiscalYear:
    fy = FiscalYear(name=name, start_date=start, end_date=end, status=status)
    db.add(fy)
    await db.commit()
    await db.refresh(fy)
    return fy


async def _create_contact(db: AsyncSession, nom: str = "Dupont") -> Contact:
    c = Contact(type=ContactType.CLIENT, nom=nom, is_active=True)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------


class TestMonthHelpers:
    def test_month_start(self) -> None:
        assert _month_start(date(2024, 6, 15)) == date(2024, 6, 1)

    def test_next_month(self) -> None:
        assert _next_month(date(2024, 1, 1)) == date(2024, 2, 1)
        assert _next_month(date(2024, 12, 1)) == date(2025, 1, 1)

    def test_shift_month_forward(self) -> None:
        assert _shift_month(date(2024, 10, 1), 3) == date(2025, 1, 1)

    def test_shift_month_backward(self) -> None:
        assert _shift_month(date(2024, 3, 1), -5) == date(2023, 10, 1)

    def test_shift_month_backward_across_year(self) -> None:
        assert _shift_month(date(2024, 1, 1), -12) == date(2023, 1, 1)


# ---------------------------------------------------------------------------
# get_dashboard
# ---------------------------------------------------------------------------


class TestGetDashboard:
    @pytest.mark.asyncio
    async def test_empty_database(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2024, 6, 15)

        monkeypatch.setattr(dashboard_module, "date", _FakeDate)

        result = await get_dashboard(db_session)

        assert result["bank_balance"] == Decimal("0")
        assert result["cash_balance"] == Decimal("0")
        assert result["unpaid_count"] == 0
        assert result["unpaid_total"] == Decimal("0")
        assert result["overdue_count"] == 0
        assert result["overdue_total"] == Decimal("0")
        assert result["undeposited_count"] == 0
        assert result["current_fy_name"] is None
        assert result["current_resultat"] == Decimal("0")
        assert result["alerts"] == []

    @pytest.mark.asyncio
    async def test_bank_and_cash_balances(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2024, 6, 15)

        monkeypatch.setattr(dashboard_module, "date", _FakeDate)

        db_session.add(
            BankTransaction(
                date=date(2024, 6, 1),
                amount=Decimal("1000.00"),
                balance_after=Decimal("5000.00"),
            )
        )
        db_session.add(
            CashRegister(
                date=date(2024, 6, 1),
                amount=Decimal("200.00"),
                type=CashMovementType.IN,
                balance_after=Decimal("200.00"),
            )
        )
        await db_session.commit()

        result = await get_dashboard(db_session)
        assert result["bank_balance"] == Decimal("5000.00")
        assert result["cash_balance"] == Decimal("200.00")

    @pytest.mark.asyncio
    async def test_unpaid_and_overdue_counts(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2024, 6, 15)

        monkeypatch.setattr(dashboard_module, "date", _FakeDate)
        contact = await _create_contact(db_session)

        # Unpaid invoice (not overdue)
        db_session.add(
            Invoice(
                number="F-001",
                type=InvoiceType.CLIENT,
                contact_id=contact.id,
                date=date(2024, 5, 1),
                due_date=date(2024, 7, 1),
                total_amount=Decimal("300.00"),
                paid_amount=Decimal("0"),
                status=InvoiceStatus.SENT,
            )
        )
        # Overdue invoice
        db_session.add(
            Invoice(
                number="F-002",
                type=InvoiceType.CLIENT,
                contact_id=contact.id,
                date=date(2024, 4, 1),
                due_date=date(2024, 5, 31),
                total_amount=Decimal("500.00"),
                paid_amount=Decimal("100.00"),
                status=InvoiceStatus.PARTIAL,
            )
        )
        # Paid invoice (should not count)
        db_session.add(
            Invoice(
                number="F-003",
                type=InvoiceType.CLIENT,
                contact_id=contact.id,
                date=date(2024, 3, 1),
                total_amount=Decimal("200.00"),
                paid_amount=Decimal("200.00"),
                status=InvoiceStatus.PAID,
            )
        )
        await db_session.commit()

        result = await get_dashboard(db_session)
        assert result["unpaid_count"] == 2
        assert result["unpaid_total"] == Decimal("700.00")  # 300 + 400
        assert result["overdue_count"] == 1
        assert result["overdue_total"] == Decimal("400.00")

    @pytest.mark.asyncio
    async def test_undeposited_payments(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2024, 6, 15)

        monkeypatch.setattr(dashboard_module, "date", _FakeDate)
        contact = await _create_contact(db_session)
        inv = Invoice(
            number="F-001",
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2024, 5, 1),
            total_amount=Decimal("100.00"),
            paid_amount=Decimal("100.00"),
            status=InvoiceStatus.PAID,
        )
        db_session.add(inv)
        await db_session.flush()

        db_session.add(
            Payment(
                invoice_id=inv.id,
                contact_id=contact.id,
                amount=Decimal("100.00"),
                date=date(2024, 5, 5),
                method=PaymentMethod.CHEQUE,
                deposited=False,
            )
        )
        await db_session.commit()

        result = await get_dashboard(db_session)
        assert result["undeposited_count"] == 1

    @pytest.mark.asyncio
    async def test_alerts_generated(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2024, 6, 15)

        monkeypatch.setattr(dashboard_module, "date", _FakeDate)
        contact = await _create_contact(db_session)

        # Overdue invoice → triggers warning alert
        db_session.add(
            Invoice(
                number="F-001",
                type=InvoiceType.CLIENT,
                contact_id=contact.id,
                date=date(2024, 4, 1),
                due_date=date(2024, 5, 1),
                total_amount=Decimal("100.00"),
                paid_amount=Decimal("0"),
                status=InvoiceStatus.SENT,
            )
        )
        inv2 = Invoice(
            number="F-002",
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2024, 5, 1),
            total_amount=Decimal("50.00"),
            paid_amount=Decimal("50.00"),
            status=InvoiceStatus.PAID,
        )
        db_session.add(inv2)
        await db_session.flush()

        # Undeposited payment → triggers info alert
        db_session.add(
            Payment(
                invoice_id=inv2.id,
                contact_id=contact.id,
                amount=Decimal("50.00"),
                date=date(2024, 5, 10),
                method=PaymentMethod.CHEQUE,
                deposited=False,
            )
        )
        await db_session.commit()

        result = await get_dashboard(db_session)
        alert_types = [a["type"] for a in result["alerts"]]
        assert "warning" in alert_types
        assert "info" in alert_types

    @pytest.mark.asyncio
    async def test_current_fy_result(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2024, 6, 15)

        monkeypatch.setattr(dashboard_module, "date", _FakeDate)
        fy = await _create_fy(db_session)

        acct_charge = AccountingAccount(
            number="607000", label="Fournitures", type=AccountType.CHARGE, is_active=True
        )
        acct_produit = AccountingAccount(
            number="706110", label="Cours", type=AccountType.PRODUIT, is_active=True
        )
        db_session.add(acct_charge)
        db_session.add(acct_produit)
        await db_session.flush()

        db_session.add(
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 3, 1),
                account_number="607000",
                label="Charge",
                debit=Decimal("200.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        db_session.add(
            AccountingEntry(
                entry_number="000002",
                date=date(2024, 3, 1),
                account_number="706110",
                label="Produit",
                debit=Decimal("0"),
                credit=Decimal("800.00"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        result = await get_dashboard(db_session)
        assert result["current_fy_name"] == "2024"
        assert result["current_resultat"] == Decimal("600.00")  # 800 - 200


# ---------------------------------------------------------------------------
# get_monthly_chart
# ---------------------------------------------------------------------------


class TestGetMonthlyChart:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_fiscal_year(self, db_session: AsyncSession) -> None:
        result = await get_monthly_chart(db_session, fiscal_year_id=None)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_monthly_breakdown(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session, start=date(2024, 1, 1), end=date(2024, 12, 31))

        acct_charge = AccountingAccount(
            number="607000", label="Fournitures", type=AccountType.CHARGE, is_active=True
        )
        acct_produit = AccountingAccount(
            number="706110", label="Cours", type=AccountType.PRODUIT, is_active=True
        )
        db_session.add(acct_charge)
        db_session.add(acct_produit)
        await db_session.flush()

        db_session.add(
            AccountingEntry(
                entry_number="000001",
                date=date(2024, 3, 15),
                account_number="607000",
                label="Charge mars",
                debit=Decimal("100.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        db_session.add(
            AccountingEntry(
                entry_number="000002",
                date=date(2024, 3, 20),
                account_number="706110",
                label="Produit mars",
                debit=Decimal("0"),
                credit=Decimal("500.00"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        result = await get_monthly_chart(db_session, fiscal_year_id=fy.id)
        assert len(result) == 12  # 12 months in the year

        march = next(r for r in result if r["month"] == "2024-03")
        assert march["charges"] == Decimal("100.00")
        assert march["produits"] == Decimal("500.00")

        # Empty month should have zeros
        january = next(r for r in result if r["month"] == "2024-01")
        assert january["charges"] == Decimal("0")
        assert january["produits"] == Decimal("0")

    @pytest.mark.asyncio
    async def test_ignores_entries_outside_fy(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session, start=date(2024, 1, 1), end=date(2024, 12, 31))
        acct = AccountingAccount(
            number="607000", label="Fournitures", type=AccountType.CHARGE, is_active=True
        )
        db_session.add(acct)
        await db_session.flush()

        # Entry outside FY
        db_session.add(
            AccountingEntry(
                entry_number="000001",
                date=date(2023, 12, 31),
                account_number="607000",
                label="Before FY",
                debit=Decimal("999.00"),
                credit=Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.MANUAL,
            )
        )
        await db_session.commit()

        result = await get_monthly_chart(db_session, fiscal_year_id=fy.id)
        total_charges = sum(Decimal(str(r["charges"])) for r in result)
        assert total_charges == Decimal("0")


# ---------------------------------------------------------------------------
# get_resources_chart
# ---------------------------------------------------------------------------


class TestGetResourcesChart:
    @pytest.mark.asyncio
    async def test_returns_rows_for_each_month(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2024, 6, 15)

        monkeypatch.setattr(dashboard_module, "date", _FakeDate)

        result = await get_resources_chart(db_session, months=3)
        assert len(result) == 3
        assert all("month" in r for r in result)
        assert all("funds" in r for r in result)
        assert all("net_resources" in r for r in result)

    @pytest.mark.asyncio
    async def test_includes_client_receivables(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeDate(date):
            @classmethod
            def today(cls) -> _FakeDate:
                return cls(2024, 6, 15)

        monkeypatch.setattr(dashboard_module, "date", _FakeDate)
        contact = await _create_contact(db_session)

        inv = Invoice(
            number="F-001",
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2024, 5, 1),
            total_amount=Decimal("500.00"),
            paid_amount=Decimal("0"),
            status=InvoiceStatus.SENT,
        )
        db_session.add(inv)
        await db_session.commit()

        result = await get_resources_chart(db_session, months=3)
        # The last month should reflect client receivables
        last_row = result[-1]
        assert last_row["client_receivables"] == Decimal("500.00")
