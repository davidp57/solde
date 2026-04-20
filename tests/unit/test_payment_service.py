"""Unit tests for the payment service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank import BankTransaction
from backend.models.cash import CashEntrySource, CashMovementType, CashRegister
from backend.models.contact import Contact, ContactType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import PaymentMethod
from backend.schemas.payment import PaymentCreate, PaymentUpdate
from backend.services import payment as payment_service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_contact(db: AsyncSession) -> Contact:
    c = Contact(type=ContactType.CLIENT, nom="Dupont", prenom="Alice")
    db.add(c)
    await db.flush()
    return c


async def _make_invoice(
    db: AsyncSession,
    contact_id: int,
    total: Decimal = Decimal("100.00"),
    status: InvoiceStatus = InvoiceStatus.SENT,
) -> Invoice:
    inv = Invoice(
        number="F-2024-001",
        type=InvoiceType.CLIENT,
        contact_id=contact_id,
        date=date(2024, 1, 15),
        total_amount=total,
        paid_amount=Decimal("0"),
        status=status,
    )
    db.add(inv)
    await db.flush()
    return inv


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_payment_basic(db_session: AsyncSession) -> None:
    """Creating a payment persists it and refreshes the invoice status."""
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))

    payload = PaymentCreate(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("100.00"),
        date=date(2024, 2, 1),
        method=PaymentMethod.CHEQUE,
    )
    payment = await payment_service.create_payment(db_session, payload)

    assert payment.id is not None
    assert payment.amount == Decimal("100.00")
    assert payment.method == PaymentMethod.CHEQUE
    assert payment.deposited is False


@pytest.mark.asyncio
async def test_create_payment_sets_invoice_paid(db_session: AsyncSession) -> None:
    """Full payment sets invoice status to PAID."""
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("50.00"))

    payload = PaymentCreate(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("50.00"),
        date=date(2024, 2, 1),
        method=PaymentMethod.CHEQUE,
    )
    await payment_service.create_payment(db_session, payload)

    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PAID
    assert inv.paid_amount == Decimal("50.00")


@pytest.mark.asyncio
async def test_create_payment_client_virement_is_rejected(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("50.00"))

    with pytest.raises(
        ValueError,
        match="client virement payments must be created from bank reconciliation",
    ):
        await payment_service.create_payment(
            db_session,
            PaymentCreate(
                invoice_id=inv.id,
                contact_id=contact.id,
                amount=Decimal("50.00"),
                date=date(2024, 2, 1),
                method=PaymentMethod.VIREMENT,
            ),
        )


@pytest.mark.asyncio
async def test_create_payment_rejects_unknown_invoice(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)

    with pytest.raises(payment_service.InvoiceNotFoundError, match="Invoice not found"):
        await payment_service.create_payment(
            db_session,
            PaymentCreate(
                invoice_id=999999,
                contact_id=contact.id,
                amount=Decimal("50.00"),
                date=date(2024, 2, 1),
                method=PaymentMethod.CHEQUE,
            ),
        )


@pytest.mark.asyncio
async def test_create_payment_partial(db_session: AsyncSession) -> None:
    """Partial payment sets invoice status to PARTIAL."""
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))

    payload = PaymentCreate(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("40.00"),
        date=date(2024, 2, 1),
        method=PaymentMethod.ESPECES,
    )
    await payment_service.create_payment(db_session, payload)

    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PARTIAL
    assert inv.paid_amount == Decimal("40.00")

    cash_entries = list(
        (await db_session.execute(select(CashRegister).order_by(CashRegister.id.asc()))).scalars()
    )
    assert len(cash_entries) == 1
    assert cash_entries[0].amount == Decimal("40.00")
    assert cash_entries[0].type == CashMovementType.IN
    assert cash_entries[0].source == CashEntrySource.PAYMENT


@pytest.mark.asyncio
async def test_create_payment_cheque_does_not_create_treasury_entry(
    db_session: AsyncSession,
) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))

    await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("40.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
        ),
    )

    bank_transactions = list((await db_session.execute(select(BankTransaction))).scalars())
    cash_entries = list((await db_session.execute(select(CashRegister))).scalars())
    assert bank_transactions == []
    assert cash_entries == []


@pytest.mark.asyncio
async def test_update_cash_payment_rejects_amount_change(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))
    payment = await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("40.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.ESPECES,
        ),
    )

    with pytest.raises(
        ValueError,
        match="cash client payments cannot change amount after creation",
    ):
        await payment_service.update_payment(
            db_session,
            payment,
            PaymentUpdate(amount=Decimal("50.00")),
        )


@pytest.mark.asyncio
async def test_update_client_payment_rejects_method_change_between_cheque_and_cash(
    db_session: AsyncSession,
) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))
    payment = await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("40.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
        ),
    )

    with pytest.raises(
        ValueError,
        match="client cheque and cash payments cannot change method after creation",
    ):
        await payment_service.update_payment(
            db_session,
            payment,
            PaymentUpdate(method=PaymentMethod.ESPECES),
        )


@pytest.mark.asyncio
async def test_create_multiple_payments_sum(db_session: AsyncSession) -> None:
    """Multiple payments sum to set the invoice as PAID."""
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))

    for amount in [Decimal("60.00"), Decimal("40.00")]:
        payload = PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=amount,
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
        )
        await payment_service.create_payment(db_session, payload)

    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PAID


@pytest.mark.asyncio
async def test_get_payment_found(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id)
    payload = PaymentCreate(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("10.00"),
        date=date(2024, 2, 1),
        method=PaymentMethod.ESPECES,
    )
    created = await payment_service.create_payment(db_session, payload)
    found = await payment_service.get_payment(db_session, created.id)
    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_get_payment_not_found(db_session: AsyncSession) -> None:
    result = await payment_service.get_payment(db_session, 9999)
    assert result is None


@pytest.mark.asyncio
async def test_list_payments_filter_invoice(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)
    inv1 = await _make_invoice(db_session, contact.id, Decimal("100.00"))
    inv2 = Invoice(
        number="F-2024-002",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 1, 15),
        total_amount=Decimal("50.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(inv2)
    await db_session.flush()

    for inv, amount in [(inv1, Decimal("30.00")), (inv2, Decimal("20.00"))]:
        await payment_service.create_payment(
            db_session,
            PaymentCreate(
                invoice_id=inv.id,
                contact_id=contact.id,
                amount=amount,
                date=date(2024, 2, 1),
                method=PaymentMethod.CHEQUE,
            ),
        )

    payments = await payment_service.list_payments(db_session, invoice_id=inv1.id)
    assert len(payments) == 1
    assert payments[0].invoice_id == inv1.id


@pytest.mark.asyncio
async def test_list_payments_undeposited_only(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))
    p1 = await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("30.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
        ),
    )
    # manually mark one as deposited
    p1.deposited = True
    await db_session.commit()

    await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("20.00"),
            date=date(2024, 2, 2),
            method=PaymentMethod.CHEQUE,
        ),
    )

    undep = await payment_service.list_payments(db_session, undeposited_only=True)
    assert all(not p.deposited for p in undep)
    assert len(undep) == 1


@pytest.mark.asyncio
async def test_update_payment(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))
    p = await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("50.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
        ),
    )
    with pytest.raises(ValueError, match="payments cannot change amount after creation"):
        await payment_service.update_payment(db_session, p, PaymentUpdate(amount=Decimal("100.00")))


@pytest.mark.asyncio
async def test_update_payment_allows_minor_reference_and_notes_changes(
    db_session: AsyncSession,
) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))
    p = await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("50.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
            cheque_number="CHQ-001",
        ),
    )

    updated = await payment_service.update_payment(
        db_session,
        p,
        PaymentUpdate(
            cheque_number="CHQ-002",
            reference="REF-2024-001",
            notes="Correction mineure",
        ),
    )

    assert updated.amount == Decimal("50.00")
    assert updated.date == date(2024, 2, 1)
    assert updated.method == PaymentMethod.CHEQUE
    assert updated.cheque_number == "CHQ-002"
    assert updated.reference == "REF-2024-001"
    assert updated.notes == "Correction mineure"


@pytest.mark.asyncio
async def test_update_cheque_payment_rejects_date_change(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))
    payment = await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("40.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
        ),
    )

    with pytest.raises(ValueError, match="payments cannot change date after creation"):
        await payment_service.update_payment(
            db_session,
            payment,
            PaymentUpdate(date=date(2024, 2, 5)),
        )


@pytest.mark.asyncio
async def test_delete_payment_reverts_invoice(db_session: AsyncSession) -> None:
    contact = await _make_contact(db_session)
    inv = await _make_invoice(db_session, contact.id, Decimal("100.00"))
    p = await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("100.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
        ),
    )
    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PAID

    await payment_service.delete_payment(db_session, p)
    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.SENT


@pytest.mark.asyncio
async def test_disputed_invoice_not_updated(db_session: AsyncSession) -> None:
    """DISPUTED invoice status is not overwritten by a payment."""
    contact = await _make_contact(db_session)
    inv = await _make_invoice(
        db_session, contact.id, Decimal("100.00"), status=InvoiceStatus.DISPUTED
    )
    await payment_service.create_payment(
        db_session,
        PaymentCreate(
            invoice_id=inv.id,
            contact_id=contact.id,
            amount=Decimal("100.00"),
            date=date(2024, 2, 1),
            method=PaymentMethod.CHEQUE,
        ),
    )
    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.DISPUTED
