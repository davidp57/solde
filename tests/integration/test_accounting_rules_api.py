"""Integration tests for accounting rules API."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.accounting_engine import seed_default_rules


@pytest.mark.asyncio
async def test_list_rules_empty(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/accounting/rules/ returns empty list initially."""
    response = await client.get("/api/accounting/rules/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_seed_rules(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """POST /api/accounting/rules/seed inserts default rules."""
    response = await client.post("/api/accounting/rules/seed", headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["inserted"] > 0

    # Second seed is idempotent
    response2 = await client.post("/api/accounting/rules/seed", headers=auth_headers)
    assert response2.status_code == 201
    assert response2.json()["inserted"] == 0


@pytest.mark.asyncio
async def test_list_rules_after_seed(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """GET /api/accounting/rules/ returns seeded rules."""
    await seed_default_rules(db_session)

    response = await client.get("/api/accounting/rules/", headers=auth_headers)
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) > 0
    assert all("name" in r and "trigger_type" in r and "entries" in r for r in rules)


@pytest.mark.asyncio
async def test_get_rule_by_id(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """GET /api/accounting/rules/{id} returns a single rule."""
    await seed_default_rules(db_session)

    list_resp = await client.get("/api/accounting/rules/", headers=auth_headers)
    rules = list_resp.json()
    rule_id = rules[0]["id"]

    response = await client.get(f"/api/accounting/rules/{rule_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == rule_id


@pytest.mark.asyncio
async def test_get_rule_not_found(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/accounting/rules/999 returns 404."""
    response = await client.get("/api/accounting/rules/999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_rule(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """PUT /api/accounting/rules/{id} updates a rule."""
    await seed_default_rules(db_session)

    list_resp = await client.get("/api/accounting/rules/", headers=auth_headers)
    rule = list_resp.json()[0]

    response = await client.put(
        f"/api/accounting/rules/{rule['id']}",
        json={"name": "Updated Rule Name", "is_active": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Rule Name"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_rule_not_found(client: AsyncClient, auth_headers: dict) -> None:
    """PUT /api/accounting/rules/999 returns 404."""
    response = await client.put(
        "/api/accounting/rules/999",
        json={"name": "Nope"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rules_require_auth(client: AsyncClient) -> None:
    """Accounting rules endpoints require authentication."""
    response = await client.get("/api/accounting/rules/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rules_require_tresorier_or_admin(
    client: AsyncClient, secretaire_auth_headers: dict
) -> None:
    """Secretaire cannot access accounting rules."""
    response = await client.get("/api/accounting/rules/", headers=secretaire_auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_readonly_cannot_access_rules(
    client: AsyncClient, readonly_auth_headers: dict
) -> None:
    """Readonly cannot access accounting rules."""
    response = await client.get("/api/accounting/rules/", headers=readonly_auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tresorier_can_list_rules(
    client: AsyncClient, tresorier_auth_headers: dict
) -> None:
    """Tresorier can access accounting rules."""
    response = await client.get("/api/accounting/rules/", headers=tresorier_auth_headers)
    assert response.status_code == 200
