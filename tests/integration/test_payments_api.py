"""Integration tests for the payments API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import Contact, ContactType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import PaymentMethod
from backend.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_contact_invoice(db_session: AsyncSession) -> tuple[int, int]:
    c = Contact(type=ContactType.CLIENT, nom="Test")
    db_session.add(c)
    await db_session.flush()
    inv = Invoice(
        number="F-2024-001",
        type=InvoiceType.CLIENT,
        contact_id=c.id,
        date=date(2024, 1, 15),
        total_amount=Decimal("120.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(inv)
    await db_session.commit()
    return c.id, inv.id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_payment_201(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    response = await client.post(
        "/api/payments/",
        json={
            "invoice_id": invoice_id,
            "contact_id": contact_id,
            "amount": "60.00",
            "date": "2024-03-01",
            "method": PaymentMethod.CHEQUE,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "60.00"
    assert data["deposited"] is False


@pytest.mark.asyncio
async def test_create_payment_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    response = await client.post(
        "/api/payments/",
        json={
            "invoice_id": invoice_id,
            "contact_id": contact_id,
            "amount": "60.00",
            "date": "2024-03-01",
            "method": "cheque",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_payments_empty(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.get("/api/payments/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_payment_not_found(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.get("/api/payments/9999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_payment(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    create_resp = await client.post(
        "/api/payments/",
        json={
            "invoice_id": invoice_id,
            "contact_id": contact_id,
            "amount": "60.00",
            "date": "2024-03-01",
            "method": "cheque",
        },
        headers=auth_headers,
    )
    payment_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/payments/{payment_id}",
        json={"amount": "80.00"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["amount"] == "80.00"


@pytest.mark.asyncio
async def test_delete_payment(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    create_resp = await client.post(
        "/api/payments/",
        json={
            "invoice_id": invoice_id,
            "contact_id": contact_id,
            "amount": "60.00",
            "date": "2024-03-01",
            "method": "cheque",
        },
        headers=auth_headers,
    )
    payment_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/payments/{payment_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/payments/{payment_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_payments_filter_undeposited(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    await client.post(
        "/api/payments/",
        json={
            "invoice_id": invoice_id,
            "contact_id": contact_id,
            "amount": "60.00",
            "date": "2024-03-01",
            "method": "cheque",
        },
        headers=auth_headers,
    )
    response = await client.get(
        "/api/payments/",
        params={"undeposited_only": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["deposited"] is False
