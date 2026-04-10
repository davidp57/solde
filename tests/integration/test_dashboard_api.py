"""Integration tests for dashboard API."""

import pytest
from httpx import AsyncClient


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
async def test_monthly_chart_returns_list(
    client: AsyncClient, auth_headers: dict
) -> None:
    """GET /api/dashboard/chart/monthly returns a list."""
    response = await client.get(
        "/api/dashboard/chart/monthly?year=2025", headers=auth_headers
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_monthly_chart_requires_auth(client: AsyncClient) -> None:
    """Monthly chart endpoint requires authentication."""
    response = await client.get("/api/dashboard/chart/monthly?year=2025")
    assert response.status_code == 401
