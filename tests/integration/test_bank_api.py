"""Integration tests for the bank API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.cash import CashEntrySource, CashMovementType, CashRegister
from backend.models.contact import Contact, ContactType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.models.user import User


def _shift_month(value: date, months: int) -> date:
    year = value.year
    month = value.month + months
    while month <= 0:
        year -= 1
        month += 12
    while month > 12:
        year += 1
        month -= 12
    return date(year, month, 1)


def _month_fixture(months_ago: int, day: int = 10) -> date:
    month_start = _shift_month(date.today().replace(day=1), -months_ago)
    return month_start.replace(day=day)


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


async def _make_client_invoice(
    db_session: AsyncSession,
    *,
    number: str = "F-2024-101",
    total_amount: Decimal = Decimal("150.00"),
) -> Invoice:
    contact = Contact(type=ContactType.CLIENT, nom="Virement Client")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number=number,
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=total_amount,
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice


async def _make_client_virement_payment(
    db_session: AsyncSession,
    *,
    number: str = "F-2024-103",
    amount: Decimal = Decimal("150.00"),
) -> Payment:
    invoice = await _make_client_invoice(
        db_session,
        number=number,
        total_amount=amount,
    )
    payment = Payment(
        invoice_id=invoice.id,
        contact_id=invoice.contact_id,
        amount=amount,
        date=date(2024, 3, 14),
        method=PaymentMethod.VIREMENT,
        reference="LEGACY-VIR-001",
        deposited=False,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


async def _make_supplier_invoice(
    db_session: AsyncSession,
    *,
    number: str = "A-2024-001",
    total_amount: Decimal = Decimal("200.00"),
) -> Invoice:
    contact = Contact(type=ContactType.FOURNISSEUR, nom="Fournisseur Test")
    db_session.add(contact)
    await db_session.flush()

    invoice = Invoice(
        number=number,
        type=InvoiceType.FOURNISSEUR,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=total_amount,
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
        reference="FAC-FOURN-001",
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice


async def _make_supplier_virement_payment(
    db_session: AsyncSession,
    *,
    amount: Decimal = Decimal("200.00"),
) -> Payment:
    invoice = await _make_supplier_invoice(db_session, total_amount=amount)
    payment = Payment(
        invoice_id=invoice.id,
        contact_id=invoice.contact_id,
        amount=amount,
        date=date(2024, 3, 14),
        method=PaymentMethod.VIREMENT,
        reference="FOURN-VIR-001",
        deposited=False,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


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
async def test_bank_funds_chart_returns_last_six_month_closing_balances(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    fixtures = [
        (_month_fixture(5, 5), "100.00"),
        (_month_fixture(3, 8), "50.00"),
        (_month_fixture(1, 12), "-20.00"),
    ]
    for tx_date, amount in fixtures:
        response = await client.post(
            "/api/bank/transactions",
            json={"date": tx_date.isoformat(), "amount": amount},
            headers=auth_headers,
        )
        assert response.status_code == 201

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="BANK-SAV-001",
                date=_month_fixture(4, 6),
                account_number="512102",
                label="Epargne ouverture",
                debit=Decimal("80.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=None,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAV-002",
                date=_month_fixture(1, 14),
                account_number="512102",
                label="Retrait epargne",
                debit=Decimal("0.00"),
                credit=Decimal("30.00"),
                fiscal_year_id=None,
                source_type=EntrySourceType.MANUAL,
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/bank/chart/funds", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert [row["month"] for row in data] == [
        _shift_month(date.today().replace(day=1), offset).strftime("%Y-%m")
        for offset in range(-5, 1)
    ]
    assert [Decimal(str(row["current_account"])) for row in data] == [
        Decimal("100.00"),
        Decimal("100.00"),
        Decimal("150.00"),
        Decimal("150.00"),
        Decimal("130.00"),
        Decimal("130.00"),
    ]
    assert [Decimal(str(row["savings_account"])) for row in data] == [
        Decimal("0.00"),
        Decimal("80.00"),
        Decimal("80.00"),
        Decimal("80.00"),
        Decimal("50.00"),
        Decimal("50.00"),
    ]
    assert [Decimal(str(row["total"])) for row in data] == [
        Decimal("100.00"),
        Decimal("180.00"),
        Decimal("230.00"),
        Decimal("230.00"),
        Decimal("180.00"),
        Decimal("180.00"),
    ]


@pytest.mark.asyncio
async def test_bank_funds_chart_uses_latest_fiscal_year_opening_for_savings_balance(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    fixtures = [
        (_month_fixture(5, 5), "100.00"),
        (_month_fixture(3, 8), "50.00"),
        (_month_fixture(1, 12), "-20.00"),
    ]
    for tx_date, amount in fixtures:
        response = await client.post(
            "/api/bank/transactions",
            json={"date": tx_date.isoformat(), "amount": amount},
            headers=auth_headers,
        )
        assert response.status_code == 201

    db_session.add_all(
        [
            AccountingEntry(
                entry_number="BANK-SAV-OPEN-2024",
                date=_month_fixture(7, 2),
                account_number="512102",
                label="Ouverture de l'exercice comptable 2024",
                debit=Decimal("100.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=2,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAV-INT-2024",
                date=_month_fixture(6, 3),
                account_number="512102",
                label="Interets livret 2024",
                debit=Decimal("20.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=2,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAV-OPEN-2025",
                date=_month_fixture(4, 2),
                account_number="512102",
                label="Ouverture de l'exercice comptable 2025",
                debit=Decimal("120.00"),
                credit=Decimal("0.00"),
                fiscal_year_id=3,
                source_type=EntrySourceType.MANUAL,
            ),
            AccountingEntry(
                entry_number="BANK-SAV-TRF-2026",
                date=_month_fixture(1, 14),
                account_number="512102",
                label="Virement interne",
                debit=Decimal("0.00"),
                credit=Decimal("30.00"),
                fiscal_year_id=3,
                source_type=EntrySourceType.GESTION,
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/bank/chart/funds", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert [Decimal(str(row["savings_account"])) for row in data] == [
        Decimal("120.00"),
        Decimal("120.00"),
        Decimal("120.00"),
        Decimal("120.00"),
        Decimal("90.00"),
        Decimal("90.00"),
    ]
    assert [Decimal(str(row["total"])) for row in data] == [
        Decimal("220.00"),
        Decimal("220.00"),
        Decimal("270.00"),
        Decimal("270.00"),
        Decimal("220.00"),
        Decimal("220.00"),
    ]


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
    assert data["confirmed"] is False
    assert data["confirmed_date"] is None

    # Payment must be in_deposit=True (en transit) but NOT deposited yet
    payment = await db_session.get(Payment, payment_id)
    assert payment is not None
    await db_session.refresh(payment)
    assert payment.in_deposit is True
    assert payment.deposited is False


@pytest.mark.asyncio
async def test_confirm_deposit(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment_id = await _make_payment(db_session)
    create_response = await client.post(
        "/api/bank/deposits",
        json={
            "date": "2024-03-01",
            "type": "cheques",
            "payment_ids": [payment_id],
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    deposit_id = create_response.json()["id"]

    confirm_response = await client.post(
        f"/api/bank/deposits/{deposit_id}/confirm",
        headers=auth_headers,
    )
    assert confirm_response.status_code == 200
    data = confirm_response.json()
    assert data["confirmed"] is True
    assert data["confirmed_date"] is not None

    # Payment must now be fully deposited and no longer in transit
    payment = await db_session.get(Payment, payment_id)
    assert payment is not None
    await db_session.refresh(payment)
    assert payment.deposited is True
    assert payment.in_deposit is False


@pytest.mark.asyncio
async def test_confirm_deposit_already_confirmed(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment_id = await _make_payment(db_session)
    create_response = await client.post(
        "/api/bank/deposits",
        json={
            "date": "2024-03-01",
            "type": "cheques",
            "payment_ids": [payment_id],
        },
        headers=auth_headers,
    )
    deposit_id = create_response.json()["id"]
    await client.post(f"/api/bank/deposits/{deposit_id}/confirm", headers=auth_headers)
    response = await client.post(
        f"/api/bank/deposits/{deposit_id}/confirm",
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_confirm_deposit_not_found(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    response = await client.post("/api/bank/deposits/9999/confirm", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_deposits_filter_by_confirmed(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment_id = await _make_payment(db_session)
    create_response = await client.post(
        "/api/bank/deposits",
        json={"date": "2024-03-01", "type": "cheques", "payment_ids": [payment_id]},
        headers=auth_headers,
    )
    deposit_id = create_response.json()["id"]

    pending_response = await client.get(
        "/api/bank/deposits", params={"confirmed": "false"}, headers=auth_headers
    )
    assert any(d["id"] == deposit_id for d in pending_response.json())

    await client.post(f"/api/bank/deposits/{deposit_id}/confirm", headers=auth_headers)

    confirmed_response = await client.get(
        "/api/bank/deposits", params={"confirmed": "true"}, headers=auth_headers
    )
    assert any(d["id"] == deposit_id for d in confirmed_response.json())

    still_pending_response = await client.get(
        "/api/bank/deposits", params={"confirmed": "false"}, headers=auth_headers
    )
    assert all(d["id"] != deposit_id for d in still_pending_response.json())


@pytest.mark.asyncio
async def test_create_especes_deposit(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    """Creating an especes deposit only requires total_amount (no payment_ids)."""
    response = await client.post(
        "/api/bank/deposits",
        json={
            "date": "2024-03-05",
            "type": "especes",
            "total_amount": "80.00",
            "bank_reference": "ESP-001",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_amount"] == "80.00"
    assert data["payment_ids"] == []
    assert data["confirmed"] is False
    assert data["denomination_details"] is None


@pytest.mark.asyncio
async def test_create_especes_deposit_with_denominations(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    """Denomination details are stored and returned as-is."""
    import json as json_mod

    denoms = json_mod.dumps([{"value": 50, "count": 1}, {"value": 20, "count": 2}])
    response = await client.post(
        "/api/bank/deposits",
        json={
            "date": "2024-03-05",
            "type": "especes",
            "total_amount": "90.00",
            "denomination_details": denoms,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["denomination_details"] == denoms


@pytest.mark.asyncio
async def test_especes_payment_auto_deposited(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    """Cash payments (especes) must be deposited=True immediately on creation."""
    c = Contact(type=ContactType.CLIENT, nom="Cash Auto")
    db_session.add(c)
    await db_session.flush()
    inv = Invoice(
        number="F-2024-ESP-01",
        type=InvoiceType.CLIENT,
        contact_id=c.id,
        date=date(2024, 1, 15),
        total_amount=Decimal("60.00"),
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
            "amount": "60.00",
            "date": "2024-03-01",
            "method": "especes",
        },
        headers=auth_headers,
    )
    assert payment_response.status_code == 201
    data = payment_response.json()
    assert data["deposited"] is True
    assert data["deposit_date"] == "2024-03-01"


@pytest.mark.asyncio
async def test_confirm_especes_deposit_creates_cash_out_entry(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    """Confirming a cash deposit creates a CashEntry OUT (caisse → banque)."""
    create_resp = await client.post(
        "/api/bank/deposits",
        json={"date": "2024-03-05", "type": "especes", "total_amount": "80.00"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    deposit_id = create_resp.json()["id"]

    # No CashEntry yet
    entries_before = list(
        (await db_session.execute(select(CashRegister).order_by(CashRegister.id.asc()))).scalars()
    )
    assert all(e.source != CashEntrySource.DEPOSIT for e in entries_before)

    confirm_resp = await client.post(
        f"/api/bank/deposits/{deposit_id}/confirm",
        headers=auth_headers,
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["confirmed"] is True

    entries_after = list(
        (await db_session.execute(select(CashRegister).order_by(CashRegister.id.asc()))).scalars()
    )
    cash_out = [e for e in entries_after if e.source == CashEntrySource.DEPOSIT]
    assert len(cash_out) == 1
    assert cash_out[0].type == CashMovementType.OUT
    assert cash_out[0].amount == Decimal("80.00")


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
    assert data[0]["detected_category"] == "customer_payment"
    assert data[1]["amount"] == "-45.50"
    assert data[1]["detected_category"] == "sepa_debit"


@pytest.mark.asyncio
async def test_create_client_payment_from_bank_transaction(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    invoice = await _make_client_invoice(db_session)

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "150.00",
            "description": "VIR DUPONT",
            "reference": "VIR-2024-001",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    reconcile_response = await client.post(
        f"/api/bank/transactions/{tx_id}/create-client-payment",
        json={"invoice_id": invoice.id},
        headers=auth_headers,
    )

    assert reconcile_response.status_code == 201
    data = reconcile_response.json()
    assert data["reconciled"] is True
    assert data["reconciled_with"] == invoice.number
    assert data["payment_id"] is not None

    payment = await db_session.get(Payment, data["payment_id"])
    assert payment is not None
    assert payment.invoice_id == invoice.id
    assert payment.contact_id == invoice.contact_id
    assert payment.amount == Decimal("150.00")
    assert payment.date == date(2024, 3, 15)
    assert payment.method == PaymentMethod.VIREMENT
    assert payment.reference == "VIR-2024-001"


@pytest.mark.asyncio
async def test_create_client_payments_from_bank_transaction(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    contact = Contact(type=ContactType.CLIENT, nom="Virement Groupe")
    db_session.add(contact)
    await db_session.flush()

    invoice_one = Invoice(
        number="F-2024-301",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 1),
        total_amount=Decimal("70.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    invoice_two = Invoice(
        number="F-2024-302",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 3, 2),
        total_amount=Decimal("50.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add_all([invoice_one, invoice_two])
    await db_session.commit()
    await db_session.refresh(invoice_one)
    await db_session.refresh(invoice_two)

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "120.00",
            "description": "VIR CLIENT GROUPE",
            "reference": "VIR-2024-002",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    reconcile_response = await client.post(
        f"/api/bank/transactions/{tx_id}/create-client-payments",
        json={
            "allocations": [
                {"invoice_id": invoice_one.id, "amount": "70.00"},
                {"invoice_id": invoice_two.id, "amount": "50.00"},
            ]
        },
        headers=auth_headers,
    )

    assert reconcile_response.status_code == 201
    data = reconcile_response.json()
    assert data["reconciled"] is True
    assert data["payment_id"] is None
    assert len(data["payment_ids"]) == 2

    payments = list(
        (
            await db_session.execute(
                select(Payment)
                .where(Payment.id.in_(data["payment_ids"]))
                .order_by(Payment.id.asc())
            )
        ).scalars()
    )
    assert [payment.invoice_id for payment in payments] == [invoice_one.id, invoice_two.id]
    assert all(payment.method == PaymentMethod.VIREMENT for payment in payments)
    assert all(payment.deposited is True for payment in payments)
    assert all(payment.deposit_date == date(2024, 3, 15) for payment in payments)

    await db_session.refresh(invoice_one)
    await db_session.refresh(invoice_two)
    assert invoice_one.status == InvoiceStatus.PAID
    assert invoice_two.status == InvoiceStatus.PAID


@pytest.mark.asyncio
async def test_create_client_payment_from_debit_transaction_is_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    invoice = await _make_client_invoice(
        db_session,
        number="F-2024-102",
        total_amount=Decimal("45.50"),
    )

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "-45.50",
            "description": "PRLV EDF",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    reconcile_response = await client.post(
        f"/api/bank/transactions/{tx_id}/create-client-payment",
        json={"invoice_id": invoice.id},
        headers=auth_headers,
    )

    assert reconcile_response.status_code == 422
    assert (
        reconcile_response.json()["detail"]
        == "only positive bank transactions can create client payments"
    )


@pytest.mark.asyncio
async def test_link_existing_client_payment_to_bank_transaction(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment = await _make_client_virement_payment(db_session)

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "150.00",
            "description": "VIR DUPONT",
            "reference": "VIR-2024-001",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    link_response = await client.post(
        f"/api/bank/transactions/{tx_id}/link-client-payment",
        json={"payment_id": payment.id},
        headers=auth_headers,
    )

    assert link_response.status_code == 200
    data = link_response.json()
    assert data["reconciled"] is True
    assert data["payment_id"] == payment.id

    await db_session.refresh(payment)
    assert payment.deposited is True
    assert payment.deposit_date == date(2024, 3, 15)


@pytest.mark.asyncio
async def test_link_existing_client_payments_to_bank_transaction(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment_one = await _make_client_virement_payment(
        db_session,
        number="F-2024-104",
        amount=Decimal("70.00"),
    )
    payment_two = await _make_client_virement_payment(
        db_session,
        number="F-2024-105",
        amount=Decimal("50.00"),
    )

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "120.00",
            "description": "VIR DUPONT GROUPE",
            "reference": "VIR-2024-003",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    link_response = await client.post(
        f"/api/bank/transactions/{tx_id}/link-client-payments",
        json={"payment_ids": [payment_one.id, payment_two.id]},
        headers=auth_headers,
    )

    assert link_response.status_code == 200
    data = link_response.json()
    assert data["reconciled"] is True
    assert data["payment_id"] is None
    assert data["payment_ids"] == [payment_one.id, payment_two.id]

    await db_session.refresh(payment_one)
    await db_session.refresh(payment_two)
    assert payment_one.deposited is True
    assert payment_two.deposited is True
    assert payment_one.deposit_date == date(2024, 3, 15)
    assert payment_two.deposit_date == date(2024, 3, 15)


@pytest.mark.asyncio
async def test_link_existing_client_payments_rejects_amount_mismatch(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment = await _make_client_virement_payment(db_session, amount=Decimal("100.00"))

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "120.00",
            "description": "VIR DUPONT GROUPE",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    link_response = await client.post(
        f"/api/bank/transactions/{tx_id}/link-client-payments",
        json={"payment_ids": [payment.id]},
        headers=auth_headers,
    )

    assert link_response.status_code == 422
    assert (
        link_response.json()["detail"] == "linked payments total must match bank transaction amount"
    )


@pytest.mark.asyncio
async def test_link_existing_client_payment_rejects_amount_mismatch(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment = await _make_client_virement_payment(db_session, amount=Decimal("120.00"))

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "150.00",
            "description": "VIR DUPONT",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    link_response = await client.post(
        f"/api/bank/transactions/{tx_id}/link-client-payment",
        json={"payment_id": payment.id},
        headers=auth_headers,
    )

    assert link_response.status_code == 422
    assert link_response.json()["detail"] == "bank transaction amount must match payment amount"


@pytest.mark.asyncio
async def test_create_supplier_payment_from_bank_transaction(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    invoice = await _make_supplier_invoice(db_session)

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "-200.00",
            "description": "VIR FOURNISSEUR TEST",
            "reference": "FOURN-2024-001",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    reconcile_response = await client.post(
        f"/api/bank/transactions/{tx_id}/create-supplier-payment",
        json={"invoice_id": invoice.id},
        headers=auth_headers,
    )

    assert reconcile_response.status_code == 201
    data = reconcile_response.json()
    assert data["reconciled"] is True
    assert data["reconciled_with"] == invoice.number
    assert data["payment_id"] is not None

    payment = await db_session.get(Payment, data["payment_id"])
    assert payment is not None
    assert payment.invoice_id == invoice.id
    assert payment.contact_id == invoice.contact_id
    assert payment.amount == Decimal("200.00")
    assert payment.date == date(2024, 3, 15)
    assert payment.method == PaymentMethod.VIREMENT
    assert payment.reference == "FOURN-2024-001"
    assert payment.deposited is True
    assert payment.deposit_date == date(2024, 3, 15)


@pytest.mark.asyncio
async def test_link_existing_supplier_payment_to_bank_transaction(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    auth_headers: dict,
) -> None:
    payment = await _make_supplier_virement_payment(db_session)

    create_tx_response = await client.post(
        "/api/bank/transactions",
        json={
            "date": "2024-03-15",
            "amount": "-200.00",
            "description": "VIR FOURNISSEUR TEST",
            "reference": "FOURN-2024-001",
            "source": "import",
        },
        headers=auth_headers,
    )
    assert create_tx_response.status_code == 201
    tx_id = create_tx_response.json()["id"]

    link_response = await client.post(
        f"/api/bank/transactions/{tx_id}/link-supplier-payment",
        json={"payment_id": payment.id},
        headers=auth_headers,
    )

    assert link_response.status_code == 200
    data = link_response.json()
    assert data["reconciled"] is True
    assert data["payment_id"] == payment.id

    await db_session.refresh(payment)
    assert payment.deposited is True
    assert payment.deposit_date == date(2024, 3, 15)
