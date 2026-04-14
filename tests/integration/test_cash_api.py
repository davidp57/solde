"""Integration tests for the cash API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.cash import CashCount, CashMovementType, CashRegister
from backend.models.user import User


@pytest.mark.asyncio
async def test_get_balance_empty(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    response = await client.get("/api/cash/balance", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["balance"] == "0"


@pytest.mark.asyncio
async def test_add_entry_in(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    response = await client.post(
        "/api/cash/entries",
        json={
            "date": "2024-03-01",
            "amount": "150.00",
            "type": "in",
            "description": "Cotisations reçues",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["balance_after"] == "150.00"
    assert data["type"] == "in"


@pytest.mark.asyncio
async def test_secretaire_can_add_entry(
    client: AsyncClient, secretaire_user: User, secretaire_auth_headers: dict
) -> None:
    response = await client.post(
        "/api/cash/entries",
        json={
            "date": "2024-03-01",
            "amount": "150.00",
            "type": "in",
            "description": "Cotisations reçues",
        },
        headers=secretaire_auth_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_readonly_cannot_access_cash_balance(
    client: AsyncClient, readonly_user: User, readonly_auth_headers: dict
) -> None:
    response = await client.get("/api/cash/balance", headers=readonly_auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_entry_unauthenticated(client: AsyncClient) -> None:
    response = await client.post(
        "/api/cash/entries",
        json={"date": "2024-03-01", "amount": "50.00", "type": "in"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_entries(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    for amount in ["100.00", "50.00"]:
        await client.post(
            "/api/cash/entries",
            json={"date": "2024-03-01", "amount": amount, "type": "in"},
            headers=auth_headers,
        )
    response = await client.get("/api/cash/entries", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_entries_returns_all_rows_when_limit_is_omitted(
    client: AsyncClient,
    admin_user: User,
    auth_headers: dict,
    db_session: AsyncSession,
) -> None:
    db_session.add_all(
        [
            CashRegister(
                date=date(2024, 3, 1),
                amount=Decimal("10.00"),
                type=CashMovementType.IN,
                description=f"Entry {index}",
                balance_after=Decimal("10.00"),
            )
            for index in range(101)
        ]
    )
    await db_session.commit()

    response = await client.get("/api/cash/entries", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 101


@pytest.mark.asyncio
async def test_list_entries_filters_by_date_range(
    client: AsyncClient,
    admin_user: User,
    auth_headers: dict,
    db_session: AsyncSession,
) -> None:
    db_session.add_all(
        [
            CashRegister(
                date=date(2024, 1, 15),
                amount=Decimal("10.00"),
                type=CashMovementType.IN,
                description="Before range",
                balance_after=Decimal("10.00"),
            ),
            CashRegister(
                date=date(2024, 3, 15),
                amount=Decimal("20.00"),
                type=CashMovementType.IN,
                description="Inside range",
                balance_after=Decimal("30.00"),
            ),
            CashRegister(
                date=date(2024, 5, 15),
                amount=Decimal("30.00"),
                type=CashMovementType.IN,
                description="After range",
                balance_after=Decimal("60.00"),
            ),
        ]
    )
    await db_session.commit()

    response = await client.get(
        "/api/cash/entries?from_date=2024-02-01&to_date=2024-04-30",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["description"] == "Inside range"


@pytest.mark.asyncio
async def test_get_entry(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    created = await client.post(
        "/api/cash/entries",
        json={
            "date": "2024-03-01",
            "amount": "150.00",
            "type": "in",
            "reference": "CAISSE-001",
            "description": "Cotisations reçues",
        },
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/cash/entries/{created.json()['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["reference"] == "CAISSE-001"


@pytest.mark.asyncio
async def test_update_entry(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    created = await client.post(
        "/api/cash/entries",
        json={
            "date": "2024-03-01",
            "amount": "150.00",
            "type": "in",
            "reference": "CAISSE-001",
            "description": "Cotisations reçues",
        },
        headers=auth_headers,
    )

    response = await client.put(
        f"/api/cash/entries/{created.json()['id']}",
        json={
            "amount": "175.00",
            "reference": "CAISSE-001B",
            "description": "Cotisations corrigées",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == "175.00"
    assert data["reference"] == "CAISSE-001B"
    assert data["description"] == "Cotisations corrigées"


@pytest.mark.asyncio
async def test_balance_after_in_and_out(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    await client.post(
        "/api/cash/entries",
        json={"date": "2024-03-01", "amount": "200.00", "type": "in"},
        headers=auth_headers,
    )
    await client.post(
        "/api/cash/entries",
        json={"date": "2024-03-02", "amount": "80.00", "type": "out"},
        headers=auth_headers,
    )
    response = await client.get("/api/cash/balance", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["balance"] == "120.00"


@pytest.mark.asyncio
async def test_create_cash_count(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    response = await client.post(
        "/api/cash/counts",
        json={
            "date": "2024-03-01",
            "count_100": 1,
            "count_20": 2,
            "count_2": 5,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "total_counted" in data
    # 100 + 40 + 10 = 150
    assert data["total_counted"] == "150.00"


@pytest.mark.asyncio
async def test_list_cash_counts(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    await client.post(
        "/api/cash/counts",
        json={"date": "2024-03-01"},
        headers=auth_headers,
    )
    response = await client.get("/api/cash/counts", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_cash_counts_returns_all_rows_when_limit_is_omitted(
    client: AsyncClient,
    admin_user: User,
    auth_headers: dict,
    db_session: AsyncSession,
) -> None:
    db_session.add_all(
        [
            CashCount(
                date=date(2024, 3, 1),
                total_counted=Decimal("0.00"),
                balance_expected=Decimal("0.00"),
                difference=Decimal("0.00"),
            )
            for _ in range(51)
        ]
    )
    await db_session.commit()

    response = await client.get("/api/cash/counts", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 51


@pytest.mark.asyncio
async def test_list_cash_counts_filters_by_date_range(
    client: AsyncClient,
    admin_user: User,
    auth_headers: dict,
    db_session: AsyncSession,
) -> None:
    db_session.add_all(
        [
            CashCount(
                date=date(2024, 1, 31),
                total_counted=Decimal("10.00"),
                balance_expected=Decimal("10.00"),
                difference=Decimal("0.00"),
            ),
            CashCount(
                date=date(2024, 3, 31),
                total_counted=Decimal("20.00"),
                balance_expected=Decimal("20.00"),
                difference=Decimal("0.00"),
            ),
            CashCount(
                date=date(2024, 5, 31),
                total_counted=Decimal("30.00"),
                balance_expected=Decimal("30.00"),
                difference=Decimal("0.00"),
            ),
        ]
    )
    await db_session.commit()

    response = await client.get(
        "/api/cash/counts?from_date=2024-02-01&to_date=2024-04-30",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["total_counted"] == "20.00"
