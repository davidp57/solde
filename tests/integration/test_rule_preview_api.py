"""Integration tests for accounting rule preview endpoint."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.accounting_engine import seed_default_rules


@pytest.mark.asyncio
async def test_preview_rule_not_found(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/accounting/rules/999/preview",
        json={"amount": "100.00", "label": "Test"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_preview_rule_success(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """Seed default rules then preview the first one."""
    await seed_default_rules(db_session)

    # Get the first rule
    list_resp = await client.get("/api/accounting/rules/", headers=auth_headers)
    assert list_resp.status_code == 200
    rules = list_resp.json()
    assert len(rules) > 0

    first_rule_id = rules[0]["id"]

    response = await client.post(
        f"/api/accounting/rules/{first_rule_id}/preview",
        json={"amount": "250.00", "label": "Facture test"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    entries = response.json()
    assert isinstance(entries, list)
    assert len(entries) > 0

    # Each entry must have the expected fields
    for entry in entries:
        assert "account_number" in entry
        assert "label" in entry
        assert "debit" in entry
        assert "credit" in entry


@pytest.mark.asyncio
async def test_preview_rule_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/accounting/rules/1/preview",
        json={"amount": "100.00"},
    )
    assert response.status_code == 401
