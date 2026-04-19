"""Payment service — record payments, update invoice status, deposit tracking."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.cash import CashEntrySource, CashMovementType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.payment import PaymentCreate, PaymentUpdate


class InvoiceNotFoundError(LookupError):
    """Raised when a payment references an invoice that does not exist."""


async def _attach_invoice_number(db: AsyncSession, payment: Payment) -> Payment:
    """Populate transient invoice metadata used by API responses."""
    result = await db.execute(
        select(Invoice.number, Invoice.type).where(Invoice.id == payment.invoice_id)
    )
    invoice_number, invoice_type = result.one_or_none() or (None, None)
    payment.invoice_number = invoice_number
    payment.invoice_type = invoice_type
    return payment


async def create_payment(db: AsyncSession, payload: PaymentCreate) -> Payment:
    """Record a payment and update the invoice paid_amount and status."""
    invoice = await _get_invoice(db, payload.invoice_id)
    if invoice is None:
        raise InvoiceNotFoundError("Invoice not found")
    _validate_manual_client_payment_method(invoice, payload.method)
    payment = Payment(**payload.model_dump())
    db.add(payment)
    await db.flush()
    await _refresh_invoice_status(db, payload.invoice_id)
    await _create_treasury_entries_for_payment(db, payment, invoice)
    # Auto-generate accounting entries (no-op if no rules seeded)
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_payment,
    )

    await generate_entries_for_payment(db, payment, invoice.type)
    await db.commit()
    await db.refresh(payment)
    return await _attach_invoice_number(db, payment)


async def get_payment(db: AsyncSession, payment_id: int) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    return None if payment is None else await _attach_invoice_number(db, payment)


async def list_payments(
    db: AsyncSession,
    *,
    invoice_id: int | None = None,
    invoice_type: InvoiceType | None = None,
    contact_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    undeposited_only: bool = False,
    skip: int = 0,
    limit: int | None = None,
) -> list[Payment]:
    query = select(Payment)
    if invoice_id is not None:
        query = query.where(Payment.invoice_id == invoice_id)
    if invoice_type is not None:
        query = query.join(Invoice, Payment.invoice_id == Invoice.id).where(
            Invoice.type == invoice_type
        )
    if contact_id is not None:
        query = query.where(Payment.contact_id == contact_id)
    if from_date is not None:
        query = query.where(Payment.date >= from_date)
    if to_date is not None:
        query = query.where(Payment.date <= to_date)
    if undeposited_only:
        query = query.where(Payment.deposited == False)  # noqa: E712
    query = query.order_by(Payment.date.desc(), Payment.id.desc()).offset(skip)
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    payments = list(result.scalars().all())
    for payment in payments:
        await _attach_invoice_number(db, payment)
    return payments


async def update_payment(db: AsyncSession, payment: Payment, payload: PaymentUpdate) -> Payment:
    invoice = await _get_invoice(db, payment.invoice_id)
    next_method = payload.method if payload.method is not None else payment.method
    _validate_manual_client_payment_method(invoice, next_method, current_method=payment.method)
    _validate_treasury_managed_payment_update(invoice, payment, payload)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    await db.flush()
    await _refresh_invoice_status(db, payment.invoice_id)
    await db.commit()
    await db.refresh(payment)
    return await _attach_invoice_number(db, payment)


async def delete_payment(db: AsyncSession, payment: Payment) -> None:
    """Delete a payment and recalculate the invoice status."""
    invoice_id = payment.invoice_id
    await db.delete(payment)
    await db.flush()
    await _refresh_invoice_status(db, invoice_id)
    await db.commit()


async def _get_invoice_type(db: AsyncSession, invoice_id: int) -> InvoiceType | None:
    """Return the type of the invoice (CLIENT/FOURNISSEUR), or None if not found."""
    result = await db.execute(select(Invoice.type).where(Invoice.id == invoice_id))
    return result.scalar_one_or_none()


async def _get_invoice(db: AsyncSession, invoice_id: int) -> Invoice | None:
    """Return the invoice for a payment, or None if it does not exist."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    return result.scalar_one_or_none()


def _validate_manual_client_payment_method(
    invoice: Invoice | None,
    method: PaymentMethod,
    *,
    current_method: PaymentMethod | None = None,
) -> None:
    """Reject manual client virements until bank reconciliation owns that workflow."""
    if invoice is None or invoice.type != InvoiceType.CLIENT:
        return
    if method != PaymentMethod.VIREMENT:
        return
    if current_method == PaymentMethod.VIREMENT:
        return
    raise ValueError("client virement payments must be created from bank reconciliation")


def _validate_treasury_managed_payment_update(
    invoice: Invoice | None,
    payment: Payment,
    payload: PaymentUpdate,
) -> None:
    """Keep treasury-linked client payments immutable on fields that would desync journals."""
    if invoice is None or invoice.type != InvoiceType.CLIENT:
        return

    if (
        payment.method in (PaymentMethod.CHEQUE, PaymentMethod.ESPECES)
        and payload.method is not None
        and payload.method != payment.method
    ):
        raise ValueError("client cheque and cash payments cannot change method after creation")

    if payment.method == PaymentMethod.ESPECES:
        if payload.amount is not None and payload.amount != payment.amount:
            raise ValueError("cash client payments cannot change amount after creation")
        if payload.date is not None and payload.date != payment.date:
            raise ValueError("cash client payments cannot change date after creation")


async def _create_treasury_entries_for_payment(
    db: AsyncSession,
    payment: Payment,
    invoice: Invoice,
) -> None:
    """Mirror client payment receipts into the operational treasury journals."""
    if invoice.type != InvoiceType.CLIENT:
        return

    description = f"Reglement facture {invoice.number}"

    if payment.method == PaymentMethod.ESPECES:
        from backend.services.cash_service import create_cash_entry_record  # noqa: PLC0415

        await create_cash_entry_record(
            db,
            date=payment.date,
            amount=Decimal(str(payment.amount)),
            type=CashMovementType.IN,
            contact_id=payment.contact_id,
            payment_id=payment.id,
            reference=payment.reference,
            description=description,
            source=CashEntrySource.PAYMENT,
        )


async def _refresh_invoice_status(db: AsyncSession, invoice_id: int) -> None:
    """Recalculate paid_amount and derive invoice status from all payments."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if invoice is None:
        return

    payments_result = await db.execute(select(Payment).where(Payment.invoice_id == invoice_id))
    all_payments = list(payments_result.scalars().all())
    paid = sum((p.amount for p in all_payments), start=Decimal("0"))
    invoice.paid_amount = paid

    total = invoice.total_amount
    current_status = invoice.status

    # Only auto-update if not in a terminal/disputed state set manually
    if current_status not in (InvoiceStatus.DISPUTED,):
        if paid >= total:
            invoice.status = InvoiceStatus.PAID
        elif paid > 0:
            invoice.status = InvoiceStatus.PARTIAL
        elif current_status == InvoiceStatus.PAID:
            # payment deleted — revert to sent if was paid
            invoice.status = InvoiceStatus.SENT
