"""Integration tests for fiscal year endpoints — pre-close checks, open-next."""

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
    fy = FiscalYear(name=name, start_date=start_date, end_date=end_date, status=status)
    db.add(fy)
    await db.commit()
    await db.refresh(fy)
    return fy


@pytest.mark.asyncio
async def test_pre_close_checks_returns_list(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """GET /api/accounting/fiscal-years/{id}/pre-close-checks returns a list."""
    fy = await _create_fy(db_session, "2024", date(2024, 1, 1), date(2024, 12, 31))
    response = await client.get(
        f"/api/accounting/fiscal-years/{fy.id}/pre-close-checks",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_pre_close_checks_not_found(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/accounting/fiscal-years/999/pre-close-checks returns 404."""
    response = await client.get(
        "/api/accounting/fiscal-years/999/pre-close-checks",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pre_close_checks_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/accounting/fiscal-years/1/pre-close-checks")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_open_next_after_close(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """POST /api/accounting/fiscal-years/{id}/open-next creates a new FY from a closed one."""
    fy = await _create_fy(
        db_session,
        "2024",
        date(2024, 1, 1),
        date(2024, 12, 31),
        FiscalYearStatus.CLOSED,
    )

    response = await client.post(
        f"/api/accounting/fiscal-years/{fy.id}/open-next",
        json={
            "name": "2025",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "2025"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_open_next_from_open_fy_fails(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """Cannot open next FY from a FY that is still open."""
    fy = await _create_fy(db_session, "2024", date(2024, 1, 1), date(2024, 12, 31))

    response = await client.post(
        f"/api/accounting/fiscal-years/{fy.id}/open-next",
        json={
            "name": "2025",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_open_next_not_found(client: AsyncClient, auth_headers: dict) -> None:
    """POST /api/accounting/fiscal-years/999/open-next returns 404."""
    response = await client.post(
        "/api/accounting/fiscal-years/999/open-next",
        json={
            "name": "2025",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_close_nonexistent_fy_404(client: AsyncClient, auth_headers: dict) -> None:
    """POST /api/accounting/fiscal-years/999/close returns 404."""
    response = await client.post(
        "/api/accounting/fiscal-years/999/close",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_administrative_close_nonexistent_fy_404(
    client: AsyncClient, auth_headers: dict
) -> None:
    """POST /api/accounting/fiscal-years/999/close-administrative returns 404."""
    response = await client.post(
        "/api/accounting/fiscal-years/999/close-administrative",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_readonly_cannot_close_fy(
    client: AsyncClient, readonly_auth_headers: dict, db_session: AsyncSession
) -> None:
    fy = await _create_fy(db_session, "2024", date(2024, 1, 1), date(2024, 12, 31))
    response = await client.post(
        f"/api/accounting/fiscal-years/{fy.id}/close",
        headers=readonly_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_secretaire_cannot_close_fy(
    client: AsyncClient, secretaire_auth_headers: dict, db_session: AsyncSession
) -> None:
    fy = await _create_fy(db_session, "2024", date(2024, 1, 1), date(2024, 12, 31))
    response = await client.post(
        f"/api/accounting/fiscal-years/{fy.id}/close",
        headers=secretaire_auth_headers,
    )
    assert response.status_code == 403
