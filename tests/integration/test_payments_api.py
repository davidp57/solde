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
    assert data["invoice_number"] == "F-2024-001"
    assert data["invoice_type"] == "client"
    assert data["deposited"] is False


@pytest.mark.asyncio
async def test_create_payment_client_virement_is_rejected(
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
            "method": PaymentMethod.VIREMENT,
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "client virement payments must be created from bank reconciliation"
    )


@pytest.mark.asyncio
async def test_create_payment_returns_404_for_unknown_invoice(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    contact_id, _invoice_id = await _setup_contact_invoice(db_session)
    response = await client.post(
        "/api/payments/",
        json={
            "invoice_id": 999999,
            "contact_id": contact_id,
            "amount": "60.00",
            "date": "2024-03-01",
            "method": PaymentMethod.CHEQUE,
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


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
async def test_readonly_cannot_list_payments(
    client: AsyncClient, readonly_user: User, readonly_auth_headers: dict
) -> None:
    response = await client.get("/api/payments/", headers=readonly_auth_headers)
    assert response.status_code == 403


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
        json={"amount": "80.00", "reference": "REF-2024-001"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 400
    assert update_resp.json()["detail"] == "payments cannot change amount after creation"


@pytest.mark.asyncio
async def test_update_payment_allows_minor_fields(
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
            "cheque_number": "CHQ-001",
        },
        headers=auth_headers,
    )
    payment_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/payments/{payment_id}",
        json={
            "cheque_number": "CHQ-002",
            "reference": "REF-2024-001",
            "notes": "Correction mineure",
        },
        headers=auth_headers,
    )

    assert update_resp.status_code == 200
    assert update_resp.json()["amount"] == "60.00"
    assert update_resp.json()["cheque_number"] == "CHQ-002"
    assert update_resp.json()["reference"] == "REF-2024-001"
    assert update_resp.json()["notes"] == "Correction mineure"


@pytest.mark.asyncio
async def test_update_payment_rejects_manual_client_virement(
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
        json={"method": "virement"},
        headers=auth_headers,
    )

    assert update_resp.status_code == 400
    assert (
        update_resp.json()["detail"]
        == "client virement payments must be created from bank reconciliation"
    )


@pytest.mark.asyncio
async def test_update_payment_rejects_switch_between_cheque_and_cash(
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
        json={"method": "especes"},
        headers=auth_headers,
    )

    assert update_resp.status_code == 400
    assert (
        update_resp.json()["detail"]
        == "client cheque and cash payments cannot change method after creation"
    )


@pytest.mark.asyncio
async def test_update_cash_payment_rejects_amount_change(
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
            "method": "especes",
        },
        headers=auth_headers,
    )
    payment_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/payments/{payment_id}",
        json={"amount": "80.00"},
        headers=auth_headers,
    )

    assert update_resp.status_code == 400
    assert (
        update_resp.json()["detail"] == "cash client payments cannot change amount after creation"
    )


@pytest.mark.asyncio
async def test_update_cheque_payment_rejects_date_change(
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
        json={"date": "2024-03-05"},
        headers=auth_headers,
    )

    assert update_resp.status_code == 400
    assert update_resp.json()["detail"] == "payments cannot change date after creation"


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


@pytest.mark.asyncio
async def test_list_payments_filter_by_date_range(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    await client.post(
        "/api/payments/",
        json={
            "invoice_id": invoice_id,
            "contact_id": contact_id,
            "amount": "60.00",
            "date": "2024-12-31",
            "method": "cheque",
        },
        headers=auth_headers,
    )
    kept_response = await client.post(
        "/api/payments/",
        json={
            "invoice_id": invoice_id,
            "contact_id": contact_id,
            "amount": "80.00",
            "date": "2025-01-15",
            "method": "especes",
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/api/payments/?from_date=2025-01-01&to_date=2025-12-31",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == kept_response.json()["id"]


@pytest.mark.asyncio
async def test_list_payments_filter_by_invoice_type(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    client_contact_id, client_invoice_id = await _setup_contact_invoice(db_session)
    supplier_contact = Contact(type=ContactType.FOURNISSEUR, nom="Fournisseur Test")
    db_session.add(supplier_contact)
    await db_session.flush()
    supplier_invoice = Invoice(
        number="2024-F-0001",
        type=InvoiceType.FOURNISSEUR,
        contact_id=supplier_contact.id,
        date=date(2024, 2, 1),
        total_amount=Decimal("90.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(supplier_invoice)
    await db_session.commit()

    client_payment_response = await client.post(
        "/api/payments/",
        json={
            "invoice_id": client_invoice_id,
            "contact_id": client_contact_id,
            "amount": "60.00",
            "date": "2024-03-01",
            "method": "cheque",
        },
        headers=auth_headers,
    )
    await client.post(
        "/api/payments/",
        json={
            "invoice_id": supplier_invoice.id,
            "contact_id": supplier_contact.id,
            "amount": "90.00",
            "date": "2024-03-02",
            "method": "virement",
        },
        headers=auth_headers,
    )

    response = await client.get("/api/payments/?invoice_type=client", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == client_payment_response.json()["id"]
    assert data[0]["invoice_type"] == "client"
