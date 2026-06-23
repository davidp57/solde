"""Integration tests for the member-mailing feature (Lot ML).

- GET /api/contacts/active-clients — active client members (invoice OR payment in window)
- POST /api/contacts/mailing — bulk email to selected contacts
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import Contact, ContactType
from backend.models.contact_email import ContactEmail
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod

_TODAY = date.today()
_RECENT = _TODAY
_OLD = date(_TODAY.year - 1, _TODAY.month, _TODAY.day)  # > 6 months ago


async def _add_contact(
    db: AsyncSession,
    *,
    nom: str,
    type_: ContactType = ContactType.CLIENT,
    is_active: bool = True,
    email: str | None = None,
) -> Contact:
    c = Contact(nom=nom, type=type_, is_active=is_active, email=email)
    db.add(c)
    await db.flush()
    return c


async def _add_invoice(db: AsyncSession, contact: Contact, *, number: str, when: date) -> Invoice:
    inv = Invoice(
        number=number,
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=when,
        due_date=when,
        total_amount=Decimal("100.00"),
        paid_amount=Decimal("0.00"),
        status=InvoiceStatus.SENT,
    )
    db.add(inv)
    await db.flush()
    return inv


async def _add_payment(db: AsyncSession, contact: Contact, invoice: Invoice, *, when: date) -> None:
    db.add(
        Payment(
            invoice_id=invoice.id,
            contact_id=contact.id,
            amount=Decimal("50.00"),
            date=when,
            method=PaymentMethod.VIREMENT,
        )
    )
    await db.flush()


@pytest.mark.asyncio
async def test_active_clients_filters(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """Only active client/les_deux members with an email and recent activity are returned."""
    recent_inv = await _add_contact(db_session, nom="Recent Invoice", email="ri@example.org")
    await _add_invoice(db_session, recent_inv, number="F-RI-1", when=_RECENT)

    recent_pay = await _add_contact(db_session, nom="Recent Payment", email="rp@example.org")
    pay_inv = await _add_invoice(db_session, recent_pay, number="F-RP-1", when=_OLD)
    await _add_payment(db_session, recent_pay, pay_inv, when=_RECENT)

    mixed = await _add_contact(
        db_session, nom="Mixed", type_=ContactType.LES_DEUX, email="mx@example.org"
    )
    await _add_invoice(db_session, mixed, number="F-MX-1", when=_RECENT)

    # Excluded cases
    old = await _add_contact(db_session, nom="Old", email="old@example.org")
    await _add_invoice(db_session, old, number="F-OLD-1", when=_OLD)

    inactive = await _add_contact(
        db_session, nom="Inactive", is_active=False, email="in@example.org"
    )
    await _add_invoice(db_session, inactive, number="F-IN-1", when=_RECENT)

    no_email = await _add_contact(db_session, nom="No Email", email=None)
    await _add_invoice(db_session, no_email, number="F-NE-1", when=_RECENT)

    supplier = await _add_contact(
        db_session, nom="Supplier", type_=ContactType.FOURNISSEUR, email="su@example.org"
    )
    await _add_invoice(db_session, supplier, number="F-SU-1", when=_RECENT)

    await db_session.commit()

    resp = await client.get("/api/contacts/active-clients?months=6", headers=auth_headers)
    assert resp.status_code == 200
    names = {row["nom"] for row in resp.json()}
    assert names == {"Recent Invoice", "Recent Payment", "Mixed"}
    # last_activity is present (non-null by construction)
    assert all(row["last_activity"] for row in resp.json())


@pytest.mark.asyncio
async def test_active_clients_rejects_bad_months(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get("/api/contacts/active-clients?months=0", headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_mailing_sends_to_selected(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """A successful mailing reports every selected contact as sent."""
    a = await _add_contact(db_session, nom="Alpha", email="a@example.org")
    b = await _add_contact(db_session, nom="Beta", email="b@example.org")
    # Beta has a secondary address → should go in Cc
    db_session.add(ContactEmail(contact_id=b.id, email="b2@example.org", sort_order=0))
    await db_session.commit()

    captured: dict = {}

    def _fake_send(**kwargs):
        captured.update(kwargs)
        return []  # no failures

    with patch("backend.services.email_service.send_bulk_emails", side_effect=_fake_send):
        resp = await client.post(
            "/api/contacts/mailing",
            headers=auth_headers,
            json={"contact_ids": [a.id, b.id], "subject": "Bonjour {prenom}", "body": "Coucou"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["sent"] == 2
    assert data["failed"] == []
    tos = {m["to"] for m in captured["messages"]}
    assert tos == {"a@example.org", "b@example.org"}
    beta_msg = next(m for m in captured["messages"] if m["to"] == "b@example.org")
    assert beta_msg["cc"] == ["b2@example.org"]


@pytest.mark.asyncio
async def test_mailing_reports_partial_failure(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    a = await _add_contact(db_session, nom="Alpha", email="a@example.org")
    b = await _add_contact(db_session, nom="Beta", email="b@example.org")
    await db_session.commit()

    def _fake_send(**kwargs):
        return [{"ref": b.id, "error": "mailbox full"}]

    with patch("backend.services.email_service.send_bulk_emails", side_effect=_fake_send):
        resp = await client.post(
            "/api/contacts/mailing",
            headers=auth_headers,
            json={"contact_ids": [a.id, b.id], "subject": "S", "body": "B"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["sent"] == 1
    assert data["failed"] == [{"contact_id": b.id, "error": "mailbox full"}]


@pytest.mark.asyncio
async def test_mailing_smtp_not_configured(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """With no SMTP host configured, the real sender raises and the API returns 400."""
    a = await _add_contact(db_session, nom="Alpha", email="a@example.org")
    await db_session.commit()

    resp = await client.post(
        "/api/contacts/mailing",
        headers=auth_headers,
        json={"contact_ids": [a.id], "subject": "S", "body": "B"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "SMTP_NOT_CONFIGURED"
