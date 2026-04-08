"""Integration tests for the cash API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

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
