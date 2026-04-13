"""Unit tests for accounting entry service (journal, balance, ledger, résultat, manual)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.schemas.accounting_entry import ManualEntryCreate
from backend.services.accounting_entry_service import (
    create_manual_entry,
    get_balance,
    get_journal,
    get_ledger,
    get_resultat,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _add_entry(
    db: AsyncSession,
    *,
    entry_number: str,
    entry_date: date,
    account_number: str,
    label: str = "Test",
    debit: Decimal = Decimal("0"),
    credit: Decimal = Decimal("0"),
    fiscal_year_id: int | None = None,
    source_type: EntrySourceType = EntrySourceType.MANUAL,
) -> AccountingEntry:
    e = AccountingEntry(
        entry_number=entry_number,
        date=entry_date,
        account_number=account_number,
        label=label,
        debit=debit,
        credit=credit,
        fiscal_year_id=fiscal_year_id,
        source_type=source_type,
        source_id=None,
    )
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


async def _add_account(
    db: AsyncSession, number: str, label: str, account_type: AccountType
) -> AccountingAccount:
    a = AccountingAccount(number=number, label=label, type=account_type, is_active=True)
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


async def _create_fy(
    db: AsyncSession,
    name: str = "2024",
    start: date | None = None,
    end: date | None = None,
) -> FiscalYear:
    fy = FiscalYear(
        name=name,
        start_date=start or date(2024, 1, 1),
        end_date=end or date(2024, 12, 31),
        status=FiscalYearStatus.OPEN,
    )
    db.add(fy)
    await db.commit()
    await db.refresh(fy)
    return fy


# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------


class TestGetJournal:
    @pytest.mark.asyncio
    async def test_empty_journal(self, db_session: AsyncSession) -> None:
        result = await get_journal(db_session)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_entries(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 6),
            account_number="706110",
            credit=Decimal("100"),
        )
        result = await get_journal(db_session)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_filter_by_account(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 5),
            account_number="706110",
            credit=Decimal("100"),
        )
        result = await get_journal(db_session, account_number="411100")
        assert len(result) == 1
        assert result[0].account_number == "411100"

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 3, 1),
            account_number="411100",
            debit=Decimal("200"),
        )
        result = await get_journal(
            db_session, from_date=date(2024, 1, 1), to_date=date(2024, 2, 28)
        )
        assert len(result) == 1
        assert result[0].entry_number == "000001"

    @pytest.mark.asyncio
    async def test_filter_by_source_type(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
            source_type=EntrySourceType.INVOICE,
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 5),
            account_number="511200",
            debit=Decimal("100"),
            source_type=EntrySourceType.PAYMENT,
        )
        result = await get_journal(db_session, source_type=EntrySourceType.INVOICE)
        assert len(result) == 1
        assert result[0].source_type == EntrySourceType.INVOICE

    @pytest.mark.asyncio
    async def test_filter_by_fiscal_year(self, db_session: AsyncSession) -> None:
        fy = await _create_fy(db_session)
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
            fiscal_year_id=fy.id,
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("200"),
            fiscal_year_id=None,
        )
        result = await get_journal(db_session, fiscal_year_id=fy.id)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_ordered_by_date_asc(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 3, 1),
            account_number="411100",
            debit=Decimal("200"),
        )
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        result = await get_journal(db_session)
        assert result[0].entry_number == "000001"


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


class TestGetBalance:
    @pytest.mark.asyncio
    async def test_empty_balance(self, db_session: AsyncSession) -> None:
        result = await get_balance(db_session)
        assert result == []

    @pytest.mark.asyncio
    async def test_aggregates_per_account(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 6),
            account_number="411100",
            debit=Decimal("200"),
        )
        await _add_entry(
            db_session,
            entry_number="000003",
            entry_date=date(2024, 1, 7),
            account_number="706110",
            credit=Decimal("300"),
        )
        result = await get_balance(db_session)
        assert len(result) == 2
        acct_411 = next(r for r in result if r.account_number == "411100")
        assert acct_411.total_debit == Decimal("300")
        assert acct_411.total_credit == Decimal("0")
        assert acct_411.solde == Decimal("300")

    @pytest.mark.asyncio
    async def test_uses_account_label_if_available(self, db_session: AsyncSession) -> None:
        await _add_account(db_session, "411100", "Clients", AccountType.ACTIF)
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        result = await get_balance(db_session)
        assert result[0].account_label == "Clients"

    @pytest.mark.asyncio
    async def test_falls_back_to_number_when_no_account(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="999999",
            debit=Decimal("100"),
        )
        result = await get_balance(db_session)
        assert result[0].account_label == "999999"


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


class TestGetLedger:
    @pytest.mark.asyncio
    async def test_empty_ledger(self, db_session: AsyncSession) -> None:
        result = await get_ledger(db_session, "411100")
        assert result.entries == []
        assert result.closing_balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_running_balance(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 10),
            account_number="411100",
            credit=Decimal("40"),
        )
        result = await get_ledger(db_session, "411100")
        assert len(result.entries) == 2
        assert result.entries[0].running_balance == Decimal("100")
        assert result.entries[1].running_balance == Decimal("60")
        assert result.closing_balance == Decimal("60")

    @pytest.mark.asyncio
    async def test_only_returns_matching_account(self, db_session: AsyncSession) -> None:
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 5),
            account_number="706110",
            credit=Decimal("100"),
        )
        result = await get_ledger(db_session, "411100")
        assert len(result.entries) == 1

    @pytest.mark.asyncio
    async def test_account_label_used(self, db_session: AsyncSession) -> None:
        await _add_account(db_session, "411100", "Clients débiteurs", AccountType.ACTIF)
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("100"),
        )
        result = await get_ledger(db_session, "411100")
        assert result.account_label == "Clients débiteurs"

    @pytest.mark.asyncio
    async def test_filters_entries_by_fiscal_year(self, db_session: AsyncSession) -> None:
        fy_2024 = await _create_fy(
            db_session,
            "2024",
            start=date(2024, 1, 1),
            end=date(2024, 12, 31),
        )
        fy_2025 = await _create_fy(
            db_session,
            "2025",
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
        )

        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 12, 31),
            account_number="512102",
            debit=Decimal("100"),
            fiscal_year_id=fy_2024.id,
            label="Solde 2024",
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2025, 1, 1),
            account_number="512102",
            debit=Decimal("100"),
            fiscal_year_id=fy_2025.id,
            source_type=EntrySourceType.CLOTURE,
            label="RAN 2024",
        )
        await _add_entry(
            db_session,
            entry_number="000003",
            entry_date=date(2025, 2, 10),
            account_number="512102",
            credit=Decimal("30"),
            fiscal_year_id=fy_2025.id,
            label="Dépense 2025",
        )

        result = await get_ledger(db_session, "512102", fiscal_year_id=fy_2025.id)

        assert [entry.entry_number for entry in result.entries] == ["000002", "000003"]
        assert result.opening_balance == Decimal("0")
        assert result.closing_balance == Decimal("70")

    @pytest.mark.asyncio
    async def test_uses_prior_entries_as_opening_balance_within_fiscal_year(
        self, db_session: AsyncSession
    ) -> None:
        fy_2025 = await _create_fy(
            db_session,
            "2025",
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
        )

        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2025, 1, 1),
            account_number="512102",
            debit=Decimal("100"),
            fiscal_year_id=fy_2025.id,
            source_type=EntrySourceType.CLOTURE,
            label="RAN 2024",
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2025, 1, 15),
            account_number="512102",
            debit=Decimal("50"),
            fiscal_year_id=fy_2025.id,
            label="Encaissement janvier",
        )
        await _add_entry(
            db_session,
            entry_number="000003",
            entry_date=date(2025, 2, 10),
            account_number="512102",
            credit=Decimal("30"),
            fiscal_year_id=fy_2025.id,
            label="Dépense février",
        )

        result = await get_ledger(
            db_session,
            "512102",
            fiscal_year_id=fy_2025.id,
            from_date=date(2025, 2, 1),
        )

        assert result.opening_balance == Decimal("150")
        assert [entry.entry_number for entry in result.entries] == ["000003"]
        assert result.entries[0].running_balance == Decimal("120")
        assert result.closing_balance == Decimal("120")

    @pytest.mark.asyncio
    async def test_from_date_equal_to_first_entry_keeps_zero_opening_balance(
        self, db_session: AsyncSession
    ) -> None:
        fy_2025 = await _create_fy(
            db_session,
            "2025",
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
        )

        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2025, 1, 1),
            account_number="512102",
            debit=Decimal("100"),
            fiscal_year_id=fy_2025.id,
            source_type=EntrySourceType.CLOTURE,
            label="RAN 2024",
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2025, 1, 15),
            account_number="512102",
            credit=Decimal("30"),
            fiscal_year_id=fy_2025.id,
            label="Dépense janvier",
        )

        result = await get_ledger(
            db_session,
            "512102",
            fiscal_year_id=fy_2025.id,
            from_date=date(2025, 1, 1),
        )

        assert result.opening_balance == Decimal("0")
        assert [entry.entry_number for entry in result.entries] == ["000001", "000002"]

    @pytest.mark.asyncio
    async def test_from_date_before_first_entry_keeps_zero_opening_balance(
        self, db_session: AsyncSession
    ) -> None:
        fy_2025 = await _create_fy(
            db_session,
            "2025",
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
        )

        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2025, 1, 10),
            account_number="512102",
            debit=Decimal("100"),
            fiscal_year_id=fy_2025.id,
            label="Encaissement janvier",
        )

        result = await get_ledger(
            db_session,
            "512102",
            fiscal_year_id=fy_2025.id,
            from_date=date(2025, 1, 5),
        )

        assert result.opening_balance == Decimal("0")
        assert [entry.entry_number for entry in result.entries] == ["000001"]


# ---------------------------------------------------------------------------
# Compte de résultat
# ---------------------------------------------------------------------------


class TestGetResultat:
    @pytest.mark.asyncio
    async def test_empty_resultat(self, db_session: AsyncSession) -> None:
        result = await get_resultat(db_session)
        assert result.total_charges == Decimal("0")
        assert result.total_produits == Decimal("0")
        assert result.resultat == Decimal("0")

    @pytest.mark.asyncio
    async def test_charges_and_produits_aggregated(self, db_session: AsyncSession) -> None:
        await _add_account(db_session, "611100", "Sous-traitance", AccountType.CHARGE)
        await _add_account(db_session, "706110", "Cours de soutien", AccountType.PRODUIT)
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="611100",
            debit=Decimal("300"),
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 5),
            account_number="706110",
            credit=Decimal("500"),
        )
        result = await get_resultat(db_session)
        assert result.total_charges == Decimal("300")
        assert result.total_produits == Decimal("500")
        assert result.resultat == Decimal("200")  # excédent

    @pytest.mark.asyncio
    async def test_deficit_is_negative(self, db_session: AsyncSession) -> None:
        await _add_account(db_session, "611100", "Sous-traitance", AccountType.CHARGE)
        await _add_account(db_session, "706110", "Cours de soutien", AccountType.PRODUIT)
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="611100",
            debit=Decimal("600"),
        )
        await _add_entry(
            db_session,
            entry_number="000002",
            entry_date=date(2024, 1, 5),
            account_number="706110",
            credit=Decimal("400"),
        )
        result = await get_resultat(db_session)
        assert result.resultat == Decimal("-200")

    @pytest.mark.asyncio
    async def test_balance_entries_ignored(self, db_session: AsyncSession) -> None:
        """Actif/passif accounts should not appear in résultat."""
        await _add_account(db_session, "411100", "Clients", AccountType.ACTIF)
        await _add_entry(
            db_session,
            entry_number="000001",
            entry_date=date(2024, 1, 5),
            account_number="411100",
            debit=Decimal("500"),
        )
        result = await get_resultat(db_session)
        assert result.total_charges == Decimal("0")
        assert result.total_produits == Decimal("0")


# ---------------------------------------------------------------------------
# Manual entry
# ---------------------------------------------------------------------------


class TestCreateManualEntry:
    @pytest.mark.asyncio
    async def test_creates_balanced_pair(self, db_session: AsyncSession) -> None:
        payload = ManualEntryCreate(
            date=date(2024, 3, 15),
            debit_account="511200",
            credit_account="411100",
            amount=Decimal("150.00"),
            label="Test manual entry",
        )
        debit_e, credit_e = await create_manual_entry(db_session, payload)
        assert debit_e.debit == Decimal("150.00")
        assert debit_e.credit == Decimal("0")
        assert credit_e.credit == Decimal("150.00")
        assert credit_e.debit == Decimal("0")

    @pytest.mark.asyncio
    async def test_accounts_are_correct(self, db_session: AsyncSession) -> None:
        payload = ManualEntryCreate(
            date=date(2024, 3, 15),
            debit_account="611100",
            credit_account="401000",
            amount=Decimal("200.00"),
            label="Manual charge",
        )
        debit_e, credit_e = await create_manual_entry(db_session, payload)
        assert debit_e.account_number == "611100"
        assert credit_e.account_number == "401000"

    @pytest.mark.asyncio
    async def test_source_type_is_manual(self, db_session: AsyncSession) -> None:
        payload = ManualEntryCreate(
            date=date(2024, 3, 15),
            debit_account="512100",
            credit_account="411100",
            amount=Decimal("75.00"),
            label="Virement reçu",
        )
        debit_e, credit_e = await create_manual_entry(db_session, payload)
        assert debit_e.source_type == EntrySourceType.MANUAL
        assert credit_e.source_type == EntrySourceType.MANUAL

    @pytest.mark.asyncio
    async def test_entry_numbers_are_different(self, db_session: AsyncSession) -> None:
        payload = ManualEntryCreate(
            date=date(2024, 3, 15),
            debit_account="512100",
            credit_account="411100",
            amount=Decimal("75.00"),
            label="Test",
        )
        debit_e, credit_e = await create_manual_entry(db_session, payload)
        assert debit_e.entry_number != credit_e.entry_number

    @pytest.mark.asyncio
    async def test_label_propagated(self, db_session: AsyncSession) -> None:
        payload = ManualEntryCreate(
            date=date(2024, 3, 15),
            debit_account="512100",
            credit_account="411100",
            amount=Decimal("50.00"),
            label="My label",
        )
        debit_e, credit_e = await create_manual_entry(db_session, payload)
        assert debit_e.label == "My label"
        assert credit_e.label == "My label"
