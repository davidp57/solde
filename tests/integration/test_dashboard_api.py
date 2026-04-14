"""Integration tests for dashboard API."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.fiscal_year import FiscalYear, FiscalYearStatus


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
async def test_monthly_chart_returns_list(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/dashboard/chart/monthly returns a list."""
    response = await client.get("/api/dashboard/chart/monthly?year=2025", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_monthly_chart_requires_auth(client: AsyncClient) -> None:
    """Monthly chart endpoint requires authentication."""
    response = await client.get("/api/dashboard/chart/monthly?year=2025")
    assert response.status_code == 401
