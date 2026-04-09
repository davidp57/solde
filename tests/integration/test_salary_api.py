"""Integration tests for salaries API."""


import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import Contact, ContactType
from backend.models.user import User


async def _create_employee(db: AsyncSession, nom: str = "Doe", prenom: str = "John") -> Contact:
    c = Contact(type=ContactType.CLIENT, nom=nom, prenom=prenom)
    db.add(c)
    await db.flush()
    return c


@pytest.mark.asyncio
async def test_list_salaries_empty(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/salaries/ returns empty list initially."""
    response = await client.get("/api/salaries/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_salary(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    admin_user: User,
) -> None:
    """POST /api/salaries/ creates a new salary record."""
    employee = await _create_employee(db_session)
    await db_session.commit()

    payload = {
        "employee_id": employee.id,
        "month": "2025-01",
        "hours": 151.67,
        "gross": 1800.0,
        "employee_charges": 252.0,
        "employer_charges": 756.0,
        "tax": 90.0,
        "net_pay": 1458.0,
    }
    response = await client.post("/api/salaries/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["month"] == "2025-01"
    assert float(data["gross"]) == pytest.approx(1800.0)
    assert float(data["total_cost"]) == pytest.approx(2556.0)


@pytest.mark.asyncio
async def test_create_salary_invalid_month(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
) -> None:
    """POST /api/salaries/ rejects invalid month format."""
    employee = await _create_employee(db_session)
    await db_session.commit()

    payload = {
        "employee_id": employee.id,
        "month": "January 2025",
        "hours": 100.0,
        "gross": 1000.0,
        "employee_charges": 100.0,
        "employer_charges": 300.0,
        "tax": 0.0,
        "net_pay": 900.0,
    }
    response = await client.post("/api/salaries/", json=payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_salary(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    admin_user: User,
) -> None:
    """DELETE /api/salaries/{id} removes the salary."""
    employee = await _create_employee(db_session, "Smith", "Alice")
    await db_session.commit()

    payload = {
        "employee_id": employee.id,
        "month": "2025-02",
        "hours": 80.0,
        "gross": 1200.0,
        "employee_charges": 168.0,
        "employer_charges": 504.0,
        "tax": 60.0,
        "net_pay": 972.0,
    }
    create_resp = await client.post("/api/salaries/", json=payload, headers=auth_headers)
    salary_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/salaries/{salary_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/salaries/{salary_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_salary_summary(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    admin_user: User,
) -> None:
    """GET /api/salaries/summary returns monthly aggregates."""
    employee = await _create_employee(db_session, "Bernard", "Luc")
    await db_session.commit()

    for _ in range(2):
        payload = {
            "employee_id": employee.id,
            "month": "2025-03",
            "hours": 50.0,
            "gross": 1000.0,
            "employee_charges": 140.0,
            "employer_charges": 420.0,
            "tax": 0.0,
            "net_pay": 860.0,
        }
        await client.post("/api/salaries/", json=payload, headers=auth_headers)

    response = await client.get("/api/salaries/summary", headers=auth_headers)
    assert response.status_code == 200
    rows = response.json()
    march = next((r for r in rows if r["month"] == "2025-03"), None)
    assert march is not None
    assert march["count"] == 2
    assert float(march["total_gross"]) == pytest.approx(2000.0)


@pytest.mark.asyncio
async def test_salary_requires_auth(client: AsyncClient) -> None:
    """Salary endpoints require authentication."""
    response = await client.get("/api/salaries/")
    assert response.status_code == 401
