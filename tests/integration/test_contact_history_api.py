"""Integration tests for contact history and doubtful receivable endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType


@pytest.mark.asyncio
async def test_get_history_not_found(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get("/api/contacts/999/history", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_history_empty(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Dupont", prenom="Jean")
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    response = await client.get(
        f"/api/contacts/{contact.id}/history", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["invoices"] == []
    assert data["payments"] == []
    assert data["total_due"] == "0"


@pytest.mark.asyncio
async def test_mark_douteux_not_found(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/api/contacts/999/mark-douteux", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_douteux_no_balance(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """Contact with no unpaid invoices → 404 (no balance)."""
    contact = Contact(type=ContactType.CLIENT, nom="Martin")
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    response = await client.post(
        f"/api/contacts/{contact.id}/mark-douteux", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_douteux_creates_entries(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """Contact with an unpaid invoice → 416xxx/411xxx entries created."""
    from datetime import date
    from decimal import Decimal

    contact = Contact(type=ContactType.CLIENT, nom="Bernard")
    db_session.add(contact)

    fy = FiscalYear(
        name="2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        status=FiscalYearStatus.OPEN,
    )
    db_session.add(fy)
    await db_session.commit()
    await db_session.refresh(contact)

    invoice = Invoice(
        number="F2025-001",
        type=InvoiceType.CLIENT,
        status=InvoiceStatus.SENT,
        date=date(2025, 3, 1),
        contact_id=contact.id,
        total_amount=Decimal("500.00"),
        paid_amount=Decimal("0.00"),
    )
    db_session.add(invoice)
    await db_session.commit()

    response = await client.post(
        f"/api/contacts/{contact.id}/mark-douteux", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == "500.00"
    assert data["account_douteux"].startswith("416")
    assert data["account_client"].startswith("411")
