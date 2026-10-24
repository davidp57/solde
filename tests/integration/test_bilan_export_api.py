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
async def test_get_bilan_no_fiscal_year(client: AsyncClient, auth_headers: dict) -> None:
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


@pytest.mark.asyncio
async def test_export_pdf_routes_require_auth(client: AsyncClient) -> None:
    for report in ("bilan", "resultat"):
        response = await client.get(f"/api/accounting/entries/{report}/export/pdf")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_pdf_filename_carries_the_fiscal_year(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, monkeypatch
) -> None:
    """The archive file is named after its year, and slashes never reach the header."""
    from datetime import date

    from backend.services import export_service

    fy = FiscalYear(
        name="2026/2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 7, 31),
        status=FiscalYearStatus.OPEN,
    )
    db_session.add(fy)
    await db_session.commit()

    async def _fake_pdf(db, fiscal_year_id=None):  # noqa: ANN001, ANN202, ARG001
        return b"%PDF-1.7 fake"

    monkeypatch.setattr(export_service, "export_bilan_pdf", _fake_pdf)

    response = await client.get(
        f"/api/accounting/entries/bilan/export/pdf?fiscal_year_id={fy.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    disposition = response.headers["content-disposition"]
    assert "bilan_2026-2027.pdf" in disposition
    assert "/" not in disposition.split("filename=")[1]


@pytest.mark.asyncio
async def test_api_responses_are_never_cached(client: AsyncClient, auth_headers: dict) -> None:
    """No intermediary may replay accounting figures that have since changed."""
    response = await client.get("/api/accounting/entries/bilan", headers=auth_headers)
    assert response.status_code == 200
    assert "no-store" in response.headers["cache-control"]
