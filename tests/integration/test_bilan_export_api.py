"""Integration tests for the accounting bilan and CSV export endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.fiscal_year import FiscalYear, FiscalYearStatus


@pytest.mark.asyncio
async def test_get_bilan_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/accounting/entries/bilan")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_bilan_no_fiscal_year(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Without a fiscal year, bilan should return empty totals."""
    response = await client.get("/api/accounting/entries/bilan", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_actif" in data
    assert "total_passif" in data


@pytest.mark.asyncio
async def test_export_journal_csv(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    from datetime import date

    fy = FiscalYear(
        name="2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        status=FiscalYearStatus.OPEN,
    )
    db_session.add(fy)
    await db_session.commit()

    response = await client.get(
        "/api/accounting/entries/journal/export/csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_export_balance_csv(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(
        "/api/accounting/entries/balance/export/csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_export_resultat_csv(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(
        "/api/accounting/entries/resultat/export/csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_export_bilan_csv(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(
        "/api/accounting/entries/bilan/export/csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
