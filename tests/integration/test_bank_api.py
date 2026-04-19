"""Integration tests for the bank API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.cash import CashMovementType, CashRegister
from backend.models.contact import Contact, ContactType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.models.user import User


async def _make_payment(db_session: AsyncSession) -> int:
    c = Contact(type=ContactType.CLIENT, nom="Banque Test")
    db_session.add(c)
    await db_session.flush()
    inv = Invoice(
        number="F-2024-099",
        type=InvoiceType.CLIENT,
        contact_id=c.id,
        date=date(2024, 1, 15),
        total_amount=Decimal("100.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(inv)
    await db_session.flush()
    p = Payment(
        invoice_id=inv.id,
        contact_id=c.id,
        amount=Decimal("100.00"),
        date=date(2024, 2, 1),
        method=PaymentMethod.CHEQUE,
        deposited=False,
    )
    db_session.add(p)
    await db_session.commit()
    return p.id


@pytest.mark.asyncio
async def test_get_balance_empty(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    response = await client.get("/api/bank/balance", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["balance"] == "0"


@pytest.mark.asyncio
async def test_add_transaction(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-01",
            "amount": "500.00",
            "description": "Virement association",
            "balance_after": "1500.00",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "500.00"
    assert data["reconciled"] is False


@pytest.mark.asyncio
async def test_secretaire_can_add_transaction(
    client: AsyncClient, secretaire_user: User, secretaire_auth_headers: dict
) -> None:
    response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-01",
            "amount": "500.00",
            "description": "Virement association",
            "balance_after": "1500.00",
        },
        headers=secretaire_auth_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_readonly_cannot_access_bank_balance(
    client: AsyncClient, readonly_user: User, readonly_auth_headers: dict
) -> None:
    response = await client.get("/api/bank/balance", headers=readonly_auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_transactions(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    for i in range(3):
        await client.post(
            "/api/bank/transactions",
            json={"date": f"2024-03-0{i + 1}", "amount": "100.00"},
            headers=auth_headers,
        )
    response = await client.get("/api/bank/transactions", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_list_transactions_filter_by_date_range(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    await client.post(
        "/api/bank/transactions",
        json={"date": "2024-07-31", "amount": "100.00"},
        headers=auth_headers,
    )
    kept = await client.post(
        "/api/bank/transactions",
        json={"date": "2024-08-01", "amount": "200.00"},
        headers=auth_headers,
    )

    response = await client.get(
        "/api/bank/transactions?from_date=2024-08-01&to_date=2025-07-31",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == kept.json()["id"]


@pytest.mark.asyncio
async def test_update_transaction_reconcile(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    create_resp = await client.post(
        "/api/bank/transactions",
        json={"date": "2024-03-01", "amount": "200.00"},
        headers=auth_headers,
    )
    tx_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/bank/transactions/{tx_id}",
        json={"reconciled": True, "reconciled_with": "REF-999"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["reconciled"] is True


@pytest.mark.asyncio
async def test_create_deposit(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment_id = await _make_payment(db_session)
    response = await client.post(
        "/api/bank/deposits",
        json={
            "date": "2024-03-01",
            "type": "cheques",
            "payment_ids": [payment_id],
            "bank_reference": "BDX-001",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_amount"] == "100.00"
    assert payment_id in data["payment_ids"]


@pytest.mark.asyncio
async def test_create_cash_deposit_creates_cash_out_entry(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    c = Contact(type=ContactType.CLIENT, nom="Banque Especes")
    db_session.add(c)
    await db_session.flush()
    inv = Invoice(
        number="F-2024-100",
        type=InvoiceType.CLIENT,
        contact_id=c.id,
        date=date(2024, 1, 15),
        total_amount=Decimal("80.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(inv)
    await db_session.commit()

    payment_response = await client.post(
        "/api/payments/",
        json={
            "invoice_id": inv.id,
            "contact_id": c.id,
            "amount": "80.00",
            "date": "2024-03-01",
            "method": "especes",
        },
        headers=auth_headers,
    )
    assert payment_response.status_code == 201
    payment_id = payment_response.json()["id"]

    response = await client.post(
        "/api/bank/deposits",
        json={
            "date": "2024-03-05",
            "type": "especes",
            "payment_ids": [payment_id],
            "bank_reference": "ESP-001",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    cash_entries = list(
        (await db_session.execute(select(CashRegister).order_by(CashRegister.id.asc()))).scalars()
    )
    assert len(cash_entries) == 2
    assert cash_entries[0].type == CashMovementType.IN
    assert cash_entries[1].type == CashMovementType.OUT
    assert cash_entries[1].amount == Decimal("80.00")


@pytest.mark.asyncio
async def test_create_deposit_invalid_payment(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.post(
        "/api/bank/deposits",
        json={"date": "2024-03-01", "type": "cheques", "payment_ids": [99999]},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_deposit_not_found(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.get("/api/bank/deposits/9999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_import_csv(client: AsyncClient, admin_user: User, auth_headers: dict) -> None:
    csv_content = (
        "Date;Valeur;Montant;Libellé;Solde\n"
        "01/03/2024;01/03/2024;150,00;VIR DUPONT;1650,00\n"
        "05/03/2024;05/03/2024;-45,50;PRLV EDF;1604,50\n"
    )
    response = await client.post(
        "/api/bank/transactions/import-csv",
        json={"content": csv_content},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["amount"] == "150.00"
    assert data[1]["amount"] == "-45.50"
