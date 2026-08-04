"""Integration tests for the payments API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
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
        response.json()["detail"]["detail"]
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
    assert response.json()["detail"]["detail"] == "Invoice not found"


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
    assert update_resp.json()["detail"]["detail"] == "payments cannot change amount after creation"


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
        update_resp.json()["detail"]["detail"]
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
        update_resp.json()["detail"]["detail"]
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
    detail = update_resp.json()["detail"]["detail"]
    assert detail == "cash client payments cannot change amount after creation"


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
    assert update_resp.json()["detail"]["detail"] == "payments cannot change date after creation"


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


async def _mark_deposited(db: AsyncSession, payment_id: int) -> None:
    """Flag a payment as cashed in at the bank, as a confirmed deposit would."""
    from backend.models.payment import Payment

    payment = (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one()
    payment.deposited = True
    await db.flush()


@pytest.mark.asyncio
async def test_cancel_payment_refused_when_deposited(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    """A cheque cashed in at the bank is refused with its machine-readable reason code."""
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
    await _mark_deposited(db_session, payment_id)

    del_resp = await client.delete(f"/api/payments/{payment_id}", headers=auth_headers)

    assert del_resp.status_code == 409
    assert del_resp.json()["detail"]["code"] == "PAYMENT_DEPOSITED"
    get_resp = await client.get(f"/api/payments/{payment_id}", headers=auth_headers)
    assert get_resp.status_code == 200


@pytest.mark.asyncio
async def test_cancel_cash_payment_is_allowed(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    """Cash is in the till, not at the bank — a mistyped receipt can still be undone."""
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    payment_id = (
        await client.post(
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
    ).json()["id"]

    del_resp = await client.delete(f"/api/payments/{payment_id}", headers=auth_headers)

    assert del_resp.status_code == 204
    get_resp = await client.get(f"/api/payments/{payment_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_payment_forbidden_for_non_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
    secretaire_auth_headers: dict,
    tresorier_auth_headers: dict,
) -> None:
    """Cancelling is an admin-only operation."""
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

    for headers in (secretaire_auth_headers, tresorier_auth_headers):
        assert (
            await client.delete(f"/api/payments/{payment_id}", headers=headers)
        ).status_code == 403
        assert (
            await client.get(f"/api/payments/{payment_id}/cancel-preview", headers=headers)
        ).status_code == 403

    get_resp = await client.get(f"/api/payments/{payment_id}", headers=auth_headers)
    assert get_resp.status_code == 200


@pytest.mark.asyncio
async def test_cancel_preview_reports_eligibility(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    """The preview endpoint answers for both an eligible and an ineligible payment."""
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    cheque_id = (
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
    ).json()["id"]
    cash_id = (
        await client.post(
            "/api/payments/",
            json={
                "invoice_id": invoice_id,
                "contact_id": contact_id,
                "amount": "10.00",
                "date": "2024-03-01",
                "method": "especes",
            },
            headers=auth_headers,
        )
    ).json()["id"]

    ok = await client.get(f"/api/payments/{cheque_id}/cancel-preview", headers=auth_headers)
    assert ok.status_code == 200
    assert ok.json()["can_cancel"] is True
    assert ok.json()["reason_code"] is None
    assert ok.json()["deposit_id"] is None

    cash_preview = await client.get(f"/api/payments/{cash_id}/cancel-preview", headers=auth_headers)
    assert cash_preview.status_code == 200
    assert cash_preview.json()["can_cancel"] is True

    await _mark_deposited(db_session, cheque_id)
    ko = await client.get(f"/api/payments/{cheque_id}/cancel-preview", headers=auth_headers)
    assert ko.status_code == 200
    assert ko.json()["can_cancel"] is False
    assert ko.json()["reason_code"] == "PAYMENT_DEPOSITED"


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


# ---------------------------------------------------------------------------
# TEC-158 — Tests for GET /api/payments/suggest_cheque_number
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_suggest_cheque_number_returns_200_with_string(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.get(
        "/api/payments/suggest_cheque_number",
        params={"payment_date": "2024-06-15"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    value = response.json()
    assert isinstance(value, str)
    # Default template is "{date}.{seq}" where date=YYYYMMDD and seq=2 digits
    assert value == "20240615.01"


@pytest.mark.asyncio
async def test_suggest_cheque_number_uses_today_when_no_date(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    """Without payment_date the endpoint must use today's date in the result."""
    response = await client.get(
        "/api/payments/suggest_cheque_number",
        headers=auth_headers,
    )
    assert response.status_code == 200
    value = response.json()
    assert isinstance(value, str)
    # The returned number must embed today's date formatted as YYYYMMDD
    today_str = date.today().strftime("%Y%m%d")
    assert today_str in value


@pytest.mark.asyncio
async def test_suggest_cheque_number_increments_when_cheques_exist(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, auth_headers: dict
) -> None:
    """Sequence counter must advance when a cheque already exists for the same date."""
    contact_id, invoice_id = await _setup_contact_invoice(db_session)
    target_date = "2025-03-10"

    # First suggestion before any cheque
    r1 = await client.get(
        "/api/payments/suggest_cheque_number",
        params={"payment_date": target_date},
        headers=auth_headers,
    )
    first = r1.json()

    # Record a cheque payment on that date
    await client.post(
        "/api/payments/",
        json={
            "invoice_id": invoice_id,
            "contact_id": contact_id,
            "amount": "120.00",
            "date": target_date,
            "method": "cheque",
            "cheque_number": first,
        },
        headers=auth_headers,
    )

    # Second suggestion must differ (next in sequence)
    r2 = await client.get(
        "/api/payments/suggest_cheque_number",
        params={"payment_date": target_date},
        headers=auth_headers,
    )
    second = r2.json()
    assert second != first


@pytest.mark.asyncio
async def test_suggest_cheque_number_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/payments/suggest_cheque_number")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_suggest_cheque_number_forbidden_for_readonly(
    client: AsyncClient,
    readonly_user: User,
    readonly_auth_headers: dict,
) -> None:
    response = await client.get(
        "/api/payments/suggest_cheque_number",
        headers=readonly_auth_headers,
    )
    assert response.status_code == 403
