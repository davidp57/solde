"""Integration tests for the accounting API endpoints (Phase 5)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_fy(
    db: AsyncSession,
    name: str = "2024",
    status: FiscalYearStatus = FiscalYearStatus.OPEN,
) -> FiscalYear:
    fy = FiscalYear(
        name=name,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        status=status,
    )
    db.add(fy)
    await db.commit()
    await db.refresh(fy)
    return fy


async def _add_entry(
    db: AsyncSession,
    entry_number: str,
    account_number: str,
    debit: Decimal = Decimal("0"),
    credit: Decimal = Decimal("0"),
    entry_date: date = date(2024, 1, 15),
    fiscal_year_id: int | None = None,
) -> AccountingEntry:
    e = AccountingEntry(
        entry_number=entry_number,
        date=entry_date,
        account_number=account_number,
        label="Test",
        debit=debit,
        credit=credit,
        fiscal_year_id=fiscal_year_id,
        source_type=EntrySourceType.MANUAL,
    )
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


# ---------------------------------------------------------------------------
# Fiscal Year API
# ---------------------------------------------------------------------------


class TestFiscalYearAPI:
    @pytest.mark.asyncio
    async def test_create_fiscal_year(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.post(
            "/api/accounting/fiscal-years/",
            json={
                "name": "2024",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "2024"
        assert data["status"] == "open"

    @pytest.mark.asyncio
    async def test_list_fiscal_years(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        await _create_fy(db_session, "2023", FiscalYearStatus.CLOSED)
        await _create_fy(db_session, "2024")
        response = await client.get("/api/accounting/fiscal-years/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_current_fiscal_year(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        fy = await _create_fy(db_session)
        response = await client.get("/api/accounting/fiscal-years/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fy.id

    @pytest.mark.asyncio
    async def test_get_current_fiscal_year_none(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.get("/api/accounting/fiscal-years/current", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_get_fiscal_year_by_id(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        fy = await _create_fy(db_session)
        response = await client.get(f"/api/accounting/fiscal-years/{fy.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == fy.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_fiscal_year_404(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.get("/api/accounting/fiscal-years/999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_close_fiscal_year(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        fy = await _create_fy(db_session)
        response = await client.post(
            f"/api/accounting/fiscal-years/{fy.id}/close",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"

    @pytest.mark.asyncio
    async def test_close_already_closed_422(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        fy = await _create_fy(db_session, status=FiscalYearStatus.CLOSED)
        response = await client.post(
            f"/api/accounting/fiscal-years/{fy.id}/close",
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/accounting/fiscal-years/",
            json={"name": "2024", "start_date": "2024-01-01", "end_date": "2024-12-31"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Journal API
# ---------------------------------------------------------------------------


class TestJournalAPI:
    @pytest.mark.asyncio
    async def test_empty_journal(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/accounting/entries/journal", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_entries(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        await _add_entry(db_session, "000001", "411100", debit=Decimal("100"))
        response = await client.get("/api/accounting/entries/journal", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["account_number"] == "411100"

    @pytest.mark.asyncio
    async def test_filter_by_account(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        await _add_entry(db_session, "000001", "411100", debit=Decimal("100"))
        await _add_entry(db_session, "000002", "706110", credit=Decimal("100"))
        response = await client.get(
            "/api/accounting/entries/journal?account_number=411100", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/accounting/entries/journal")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Balance API
# ---------------------------------------------------------------------------


class TestBalanceAPI:
    @pytest.mark.asyncio
    async def test_empty_balance(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/accounting/entries/balance", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_aggregated_rows(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        await _add_entry(db_session, "000001", "411100", debit=Decimal("100"))
        await _add_entry(db_session, "000002", "411100", debit=Decimal("200"))
        response = await client.get("/api/accounting/entries/balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert float(data[0]["total_debit"]) == 300.0


# ---------------------------------------------------------------------------
# Ledger API
# ---------------------------------------------------------------------------


class TestLedgerAPI:
    @pytest.mark.asyncio
    async def test_empty_ledger(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/accounting/entries/ledger/411100", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entries"] == []
        assert float(data["closing_balance"]) == 0.0

    @pytest.mark.asyncio
    async def test_ledger_with_entries(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ) -> None:
        await _add_entry(
            db_session, "000001", "411100", debit=Decimal("100"), entry_date=date(2024, 1, 5)
        )
        await _add_entry(
            db_session, "000002", "411100", credit=Decimal("40"), entry_date=date(2024, 1, 10)
        )
        response = await client.get("/api/accounting/entries/ledger/411100", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 2
        assert float(data["closing_balance"]) == 60.0


# ---------------------------------------------------------------------------
# Résultat API
# ---------------------------------------------------------------------------


class TestResultatAPI:
    @pytest.mark.asyncio
    async def test_empty_resultat(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/accounting/entries/resultat", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert float(data["total_charges"]) == 0.0
        assert float(data["total_produits"]) == 0.0


# ---------------------------------------------------------------------------
# Manual Entry API
# ---------------------------------------------------------------------------


class TestManualEntryAPI:
    @pytest.mark.asyncio
    async def test_create_manual_entry(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.post(
            "/api/accounting/entries/manual",
            json={
                "date": "2024-03-15",
                "debit_account": "512100",
                "credit_account": "411100",
                "amount": "150.00",
                "label": "Remboursement",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2
        debit = next(e for e in data if float(e["debit"]) > 0)
        credit = next(e for e in data if float(e["credit"]) > 0)
        assert debit["account_number"] == "512100"
        assert credit["account_number"] == "411100"

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/accounting/entries/manual",
            json={
                "date": "2024-03-15",
                "debit_account": "512100",
                "credit_account": "411100",
                "amount": "100.00",
                "label": "Test",
            },
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Accounting Rules API
# ---------------------------------------------------------------------------


class TestAccountingRulesAPI:
    @pytest.mark.asyncio
    async def test_list_rules_empty(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/accounting/rules/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_seed_default_rules(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.post("/api/accounting/rules/seed", headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["inserted"] > 0

    @pytest.mark.asyncio
    async def test_seed_idempotent(self, client: AsyncClient, auth_headers: dict) -> None:
        await client.post("/api/accounting/rules/seed", headers=auth_headers)
        response = await client.post("/api/accounting/rules/seed", headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["inserted"] == 0

    @pytest.mark.asyncio
    async def test_list_rules_after_seed(self, client: AsyncClient, auth_headers: dict) -> None:
        await client.post("/api/accounting/rules/seed", headers=auth_headers)
        response = await client.get("/api/accounting/rules/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) > 0

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/accounting/rules/999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_rule_by_id(self, client: AsyncClient, auth_headers: dict) -> None:
        await client.post("/api/accounting/rules/seed", headers=auth_headers)
        rules = (await client.get("/api/accounting/rules/", headers=auth_headers)).json()
        rule_id = rules[0]["id"]
        response = await client.get(f"/api/accounting/rules/{rule_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == rule_id

    @pytest.mark.asyncio
    async def test_update_rule_deactivate(self, client: AsyncClient, auth_headers: dict) -> None:
        await client.post("/api/accounting/rules/seed", headers=auth_headers)
        rules = (await client.get("/api/accounting/rules/", headers=auth_headers)).json()
        rule_id = rules[0]["id"]
        response = await client.put(
            f"/api/accounting/rules/{rule_id}",
            json={"is_active": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False
