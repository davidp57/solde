"""Payment service — record payments, update invoice status, deposit tracking."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.invoice import Invoice, InvoiceStatus
from backend.models.payment import Payment
from backend.schemas.payment import PaymentCreate, PaymentUpdate


async def create_payment(db: AsyncSession, payload: PaymentCreate) -> Payment:
    """Record a payment and update the invoice paid_amount and status."""
    payment = Payment(**payload.model_dump())
    db.add(payment)
    await db.flush()
    await _refresh_invoice_status(db, payload.invoice_id)
    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payment(db: AsyncSession, payment_id: int) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def list_payments(
    db: AsyncSession,
    *,
    invoice_id: int | None = None,
    contact_id: int | None = None,
    undeposited_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[Payment]:
    query = select(Payment)
    if invoice_id is not None:
        query = query.where(Payment.invoice_id == invoice_id)
    if contact_id is not None:
        query = query.where(Payment.contact_id == contact_id)
    if undeposited_only:
        query = query.where(Payment.deposited == False)  # noqa: E712
    query = query.order_by(Payment.date.desc(), Payment.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_payment(db: AsyncSession, payment: Payment, payload: PaymentUpdate) -> Payment:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    await db.flush()
    await _refresh_invoice_status(db, payment.invoice_id)
    await db.commit()
    await db.refresh(payment)
    return payment


async def delete_payment(db: AsyncSession, payment: Payment) -> None:
    """Delete a payment and recalculate the invoice status."""
    invoice_id = payment.invoice_id
    await db.delete(payment)
    await db.flush()
    await _refresh_invoice_status(db, invoice_id)
    await db.commit()


async def _refresh_invoice_status(db: AsyncSession, invoice_id: int) -> None:
    """Recalculate paid_amount and derive invoice status from all payments."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if invoice is None:
        return

    payments_result = await db.execute(select(Payment).where(Payment.invoice_id == invoice_id))
    all_payments = list(payments_result.scalars().all())
    paid = sum(p.amount for p in all_payments) if all_payments else Decimal("0")
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
