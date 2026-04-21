"""Integration tests for dashboard API."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.bank import BankTransaction
from backend.models.cash import CashMovementType, CashRegister
from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod


async def _create_fy(
    db: AsyncSession,
    name: str,
    start_date: date,
    end_date: date,
    status: FiscalYearStatus = FiscalYearStatus.OPEN,
) -> FiscalYear:
    fy = FiscalYear(
        name=name,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )
    db.add(fy)
    await db.commit()
    await db.refresh(fy)
    return fy


def _shift_month(value: date, months: int) -> date:
    year = value.year
    month = value.month + months
    while month <= 0:
        year -= 1
        month += 12
    while month > 12:
        year += 1
        month -= 12
    return date(year, month, 1)


def _month_fixture(months_ago: int, day: int = 10) -> date:
    month_start = _shift_month(date.today().replace(day=1), -months_ago)
    return month_start.replace(day=day)


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: AsyncClient) -> None:
    """Dashboard endpoint requires authentication."""
    response = await client.get("/api/dashboard/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_returns_kpis(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/dashboard/ returns expected KPI keys."""
    response = await client.get("/api/dashboard/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "bank_balance" in data
    assert "cash_balance" in data
    assert "unpaid_count" in data
    assert "unpaid_total" in data
    assert "overdue_count" in data
    assert "overdue_total" in data
    assert "undeposited_count" in data
    assert "current_fy_name" in data
    assert "current_resultat" in data
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


@pytest.mark.asyncio
async def test_dashboard_empty_db(client: AsyncClient, auth_headers: dict) -> None:
    """Dashboard with empty DB returns zeros / None without error."""
    response = await client.get("/api/dashboard/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["unpaid_count"] == 0
    assert data["overdue_count"] == 0
    assert data["undeposited_count"] == 0


@pytest.mark.asyncio
async def test_dashboard_uses_open_fiscal_year_covering_today(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    today = date.today()
    covering_start = date(today.year, 1, 1)
    covering_end = date(today.year, 12, 31)

    await _create_fy(
        db_session,
        "older-open",
        date(today.year - 2, 1, 1),
        date(today.year - 2, 12, 31),
    )
    await _create_fy(db_session, "current-open", covering_start, covering_end)

    response = await client.get("/api/dashboard/", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["current_fy_name"] == "current-open"


@pytest.mark.asyncio
async def test_dashboard_falls_back_to_latest_open_fiscal_year(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    today = date.today()

    await _create_fy(
        db_session,
        "older-open",
        date(today.year - 3, 1, 1),
        date(today.year - 3, 12, 31),
    )
    await _create_fy(
        db_session,
        "latest-open",
        date(today.year - 1, 1, 1),
        date(today.year - 1, 12, 31),
    )

    response = await client.get("/api/dashboard/", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["current_fy_name"] == "latest-open"


@pytest.mark.asyncio
async def test_dashboard_counts_overdue_from_remaining_amount_not_only_status(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Dupont")
    db_session.add(contact)
    await db_session.flush()

    db_session.add(
        Invoice(
            number="F-TEST-0001",
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 1, 10),
            due_date=date(2025, 2, 10),
            total_amount=Decimal("120"),
            paid_amount=Decimal("20"),
            status=InvoiceStatus.DISPUTED,
        )
    )
    await db_session.commit()

    response = await client.get("/api/dashboard/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["unpaid_count"] == 1
    assert Decimal(str(data["unpaid_total"])) == Decimal("100")
    assert data["overdue_count"] == 1
    assert Decimal(str(data["overdue_total"])) == Decimal("100")


@pytest.mark.asyncio
async def test_monthly_chart_returns_list(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/dashboard/chart/monthly returns a list."""
    response = await client.get("/api/dashboard/chart/monthly", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_monthly_chart_requires_auth(client: AsyncClient) -> None:
    """Monthly chart endpoint requires authentication."""
    response = await client.get("/api/dashboard/chart/monthly")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_monthly_chart_uses_selected_fiscal_year_window(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    fiscal_year = await _create_fy(
        db_session,
        "2024/2025",
        date(2024, 8, 1),
        date(2025, 7, 31),
    )

    db_session.add_all(
        [
            AccountingAccount(number="611100", label="Charges", type=AccountType.CHARGE),
            AccountingAccount(number="706000", label="Produits", type=AccountType.PRODUIT),
            AccountingEntry(
                entry_number="E-1",
                date=date(2024, 8, 10),
                account_number="611100",
                label="Charge aout",
                debit=100,
                credit=0,
                fiscal_year_id=fiscal_year.id,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="E-2",
                date=date(2025, 2, 5),
                account_number="706000",
                label="Produit fevrier",
                debit=0,
                credit=250,
                fiscal_year_id=fiscal_year.id,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="E-3",
                date=date(2024, 7, 20),
                account_number="611100",
                label="Hors exercice",
                debit=999,
                credit=0,
                fiscal_year_id=None,
                source_type=EntrySourceType.MANUAL,
            ),
        ]
    )
    await db_session.commit()

    response = await client.get(
        f"/api/dashboard/chart/monthly?fiscal_year_id={fiscal_year.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert data[0]["month"] == "2024-08"
    assert Decimal(str(data[0]["charges"])) == Decimal("100")
    assert Decimal(str(data[0]["produits"])) == Decimal("0")
    february_row = next(row for row in data if row["month"] == "2025-02")
    assert Decimal(str(february_row["produits"])) == Decimal("250")
    assert all(row["month"] != "2024-07" for row in data)


@pytest.mark.asyncio
async def test_resources_chart_returns_last_twelve_months_with_component_totals(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    client_contact = Contact(type=ContactType.CLIENT, nom="Client Ressources")
    supplier_contact = Contact(type=ContactType.FOURNISSEUR, nom="Fournisseur Ressources")
    db_session.add_all([client_contact, supplier_contact])
    await db_session.flush()

    client_invoice_date = _month_fixture(2, 5)
    supplier_invoice_date = _month_fixture(1, 6)
    cheque_payment_date = _month_fixture(1, 12)

    client_invoice = Invoice(
        number="F-RES-001",
        type=InvoiceType.CLIENT,
        contact_id=client_contact.id,
        date=client_invoice_date,
        due_date=client_invoice_date,
        total_amount=Decimal("100.00"),
        paid_amount=Decimal("40.00"),
        status=InvoiceStatus.PARTIAL,
    )
    supplier_invoice = Invoice(
        number="A-RES-001",
        type=InvoiceType.FOURNISSEUR,
        contact_id=supplier_contact.id,
        date=supplier_invoice_date,
        due_date=supplier_invoice_date,
        total_amount=Decimal("30.00"),
        paid_amount=Decimal("0.00"),
        status=InvoiceStatus.SENT,
    )
    db_session.add_all([client_invoice, supplier_invoice])
    await db_session.flush()

    db_session.add(
        AccountingEntry(
            entry_number="IGNORED",
            date=_month_fixture(6, 10),
            account_number="706000",
            label="Pas utilise pour ce graphe",
            debit=0,
            credit=0,
            fiscal_year_id=None,
            source_type=EntrySourceType.MANUAL,
        )
    )
    db_session.add_all(
        [
            BankTransaction(
                date=client_invoice_date,
                amount=Decimal("200.00"),
                description="Fonds banque",
                balance_after=Decimal("200.00"),
                reconciled=False,
                source="manual",
                detected_category="other_credit",
            ),
            CashRegister(
                date=supplier_invoice_date,
                amount=Decimal("50.00"),
                type=CashMovementType.IN,
                description="Fonds caisse",
                balance_after=Decimal("50.00"),
            ),
            Payment(
                invoice_id=client_invoice.id,
                contact_id=client_contact.id,
                amount=Decimal("40.00"),
                date=cheque_payment_date,
                method=PaymentMethod.CHEQUE,
                deposited=False,
                deposit_date=None,
                reference="F-RES-001",
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/dashboard/chart/resources", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    expected_months = [
        _shift_month(date.today().replace(day=1), offset).strftime("%Y-%m")
        for offset in range(-11, 1)
    ]
    assert [row["month"] for row in data] == expected_months

    by_month = {row["month"]: row for row in data}
    two_months_ago = _shift_month(date.today().replace(day=1), -2).strftime("%Y-%m")
    previous_month = _shift_month(date.today().replace(day=1), -1).strftime("%Y-%m")

    assert Decimal(str(by_month[two_months_ago]["funds"])) == Decimal("200.00")
    assert Decimal(str(by_month[two_months_ago]["liquidities"])) == Decimal("200.00")
    assert Decimal(str(by_month[two_months_ago]["client_receivables"])) == Decimal("100.00")
    assert Decimal(str(by_month[two_months_ago]["undeposited_cheques"])) == Decimal("0.00")
    assert Decimal(str(by_month[two_months_ago]["supplier_payables"])) == Decimal("0.00")
    assert Decimal(str(by_month[two_months_ago]["net_resources"])) == Decimal("300.00")

    assert Decimal(str(by_month[previous_month]["funds"])) == Decimal("250.00")
    assert Decimal(str(by_month[previous_month]["liquidities"])) == Decimal("250.00")
    assert Decimal(str(by_month[previous_month]["client_receivables"])) == Decimal("60.00")
    assert Decimal(str(by_month[previous_month]["undeposited_cheques"])) == Decimal("40.00")
    assert Decimal(str(by_month[previous_month]["supplier_payables"])) == Decimal("30.00")
    assert Decimal(str(by_month[previous_month]["net_resources"])) == Decimal("320.00")


@pytest.mark.asyncio
async def test_resources_chart_uses_both_bank_accounts_in_liquidities(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    from backend.models.cash import CashMovementType, CashRegister

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="BANK-CURRENT-001",
                date=_month_fixture(1, 5),
                account_number="512100",
                label="Compte courant",
                debit=Decimal("120.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=None,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAVINGS-001",
                date=_month_fixture(1, 7),
                account_number="512102",
                label="Compte epargne",
                debit=Decimal("80.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=None,
                source_type=EntrySourceType.MANUAL,
            ),
            CashRegister(
                date=_month_fixture(1, 9),
                amount=Decimal("50.00"),
                type=CashMovementType.IN,
                description="Liquidites caisse",
                balance_after=Decimal("50.00"),
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/dashboard/chart/resources", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    previous_month = _shift_month(date.today().replace(day=1), -1).strftime("%Y-%m")
    row = next(item for item in data if item["month"] == previous_month)

    assert Decimal(str(row["funds"])) == Decimal("250.00")
    assert Decimal(str(row["liquidities"])) == Decimal("250.00")
    assert Decimal(str(row["net_resources"])) == Decimal("250.00")


@pytest.mark.asyncio
async def test_resources_chart_uses_latest_savings_opening_instead_of_accumulating_year_openings(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    from backend.models.cash import CashMovementType, CashRegister

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="BANK-CURRENT-OPEN-2025",
                date=_month_fixture(4, 2),
                account_number="512100",
                label="Ouverture de l'exercice comptable 2025",
                debit=Decimal("120.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=3,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAV-OPEN-2024",
                date=_month_fixture(7, 2),
                account_number="512102",
                label="Ouverture de l'exercice comptable 2024",
                debit=Decimal("100.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=2,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAV-INT-2024",
                date=_month_fixture(6, 3),
                account_number="512102",
                label="Interets livret 2024",
                debit=Decimal("20.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=2,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAV-OPEN-2025",
                date=_month_fixture(4, 2),
                account_number="512102",
                label="Ouverture de l'exercice comptable 2025",
                debit=Decimal("120.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=3,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAV-TRF-2026",
                date=_month_fixture(1, 14),
                account_number="512102",
                label="Virement interne",
                debit=Decimal("0.00"),
                credit=Decimal("30.00"),
                fiscal_year_id=3,
                source_type=EntrySourceType.GESTION,
            ),
            CashRegister(
                date=_month_fixture(1, 9),
                amount=Decimal("50.00"),
                type=CashMovementType.IN,
                description="Liquidites caisse",
                balance_after=Decimal("50.00"),
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/dashboard/chart/resources", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    previous_month = _shift_month(date.today().replace(day=1), -1).strftime("%Y-%m")
    row = next(item for item in data if item["month"] == previous_month)

    assert Decimal(str(row["funds"])) == Decimal("260.00")
    assert Decimal(str(row["liquidities"])) == Decimal("260.00")
    assert Decimal(str(row["net_resources"])) == Decimal("260.00")
