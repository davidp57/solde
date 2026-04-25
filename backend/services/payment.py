"""Payment service — record payments, update invoice status, deposit tracking."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models.cash import CashEntrySource, CashMovementType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate


class InvoiceNotFoundError(LookupError):
    """Raised when a payment references an invoice that does not exist."""


class PaymentDeleteError(ValueError):
    """Raised when a payment deletion is not allowed in the standard workflow."""


async def _to_payment_read(db: AsyncSession, payment: Payment) -> PaymentRead:
    """Build a PaymentRead DTO enriched with invoice metadata."""
    result = await db.execute(
        select(Invoice.number, Invoice.type).where(Invoice.id == payment.invoice_id)
    )
    row = result.one_or_none()
    invoice_number: str | None = row[0] if row else None
    invoice_type: InvoiceType | None = InvoiceType(row[1]) if row and row[1] else None
    read = PaymentRead.model_validate(payment)
    return read.model_copy(update={"invoice_number": invoice_number, "invoice_type": invoice_type})


async def _get_payment_orm(db: AsyncSession, payment_id: int) -> Payment | None:
    """Return the raw ORM Payment (no DTO enrichment)."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def create_payment(db: AsyncSession, payload: PaymentCreate) -> PaymentRead:
    """Record a payment and update the invoice paid_amount and status."""
    return await _create_payment(db, payload)


async def create_bank_reconciled_client_payment(
    db: AsyncSession,
    *,
    invoice_id: int,
    amount: Decimal,
    payment_date: date,
    reference: str | None = None,
    notes: str | None = None,
    commit: bool = True,
) -> PaymentRead:
    """Create a client virement originating from a reconciled bank transaction."""
    invoice = await _get_invoice(db, invoice_id)
    if invoice is None:
        raise InvoiceNotFoundError("Invoice not found")
    if invoice.type != InvoiceType.CLIENT:
        raise ValueError("bank reconciliation can only create client payments")

    payload = PaymentCreate(
        invoice_id=invoice.id,
        contact_id=invoice.contact_id,
        amount=amount,
        date=payment_date,
        method=PaymentMethod.VIREMENT,
        reference=reference,
        notes=notes,
    )
    return await _create_payment(
        db,
        payload,
        allow_client_virement=True,
        deposited=True,
        deposit_date=payment_date,
        commit=commit,
    )


async def create_bank_reconciled_supplier_payment(
    db: AsyncSession,
    *,
    invoice_id: int,
    amount: Decimal,
    payment_date: date,
    reference: str | None = None,
    notes: str | None = None,
    commit: bool = True,
) -> PaymentRead:
    """Create a supplier virement originating from a reconciled bank transaction."""
    invoice = await _get_invoice(db, invoice_id)
    if invoice is None:
        raise InvoiceNotFoundError("Invoice not found")
    if invoice.type != InvoiceType.FOURNISSEUR:
        raise ValueError("bank reconciliation can only create supplier payments")

    payload = PaymentCreate(
        invoice_id=invoice.id,
        contact_id=invoice.contact_id,
        amount=amount,
        date=payment_date,
        method=PaymentMethod.VIREMENT,
        reference=reference,
        notes=notes,
    )
    return await _create_payment(
        db,
        payload,
        deposited=True,
        deposit_date=payment_date,
        commit=commit,
    )


async def _create_payment(
    db: AsyncSession,
    payload: PaymentCreate,
    *,
    allow_client_virement: bool = False,
    deposited: bool | None = None,
    deposit_date: date | None = None,
    commit: bool = True,
) -> PaymentRead:
    """Persist a payment and all its side effects."""
    invoice = await _get_invoice(db, payload.invoice_id)
    if invoice is None:
        raise InvoiceNotFoundError("Invoice not found")
    _validate_manual_client_payment_method(
        invoice,
        payload.method,
        allow_client_virement=allow_client_virement,
    )
    payment = Payment(**payload.model_dump())
    if deposited is not None:
        payment.deposited = deposited
    if deposit_date is not None:
        payment.deposit_date = deposit_date
    db.add(payment)
    await db.flush()
    await _refresh_invoice_status(db, payload.invoice_id)
    await _create_treasury_entries_for_payment(db, payment, invoice)
    # Auto-generate accounting entries (no-op if no rules seeded)
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_payment,
    )

    await generate_entries_for_payment(db, payment, invoice.type)
    if commit:
        await db.commit()
        await db.refresh(payment)
    return await _to_payment_read(db, payment)


async def get_payment(db: AsyncSession, payment_id: int) -> PaymentRead | None:
    payment = await _get_payment_orm(db, payment_id)
    return None if payment is None else await _to_payment_read(db, payment)


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
    limit: int = 100,
) -> list[PaymentRead]:
    inv = aliased(Invoice)
    query = select(Payment, inv.number, inv.type).join(inv, Payment.invoice_id == inv.id)
    if invoice_id is not None:
        query = query.where(Payment.invoice_id == invoice_id)
    if invoice_type is not None:
        query = query.where(inv.type == invoice_type)
    if contact_id is not None:
        query = query.where(Payment.contact_id == contact_id)
    if from_date is not None:
        query = query.where(Payment.date >= from_date)
    if to_date is not None:
        query = query.where(Payment.date <= to_date)
    if undeposited_only:
        query = query.where(Payment.deposited == False)  # noqa: E712
    query = query.order_by(Payment.date.desc(), Payment.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    out: list[PaymentRead] = []
    for payment, inv_number, inv_type in rows:
        read = PaymentRead.model_validate(payment)
        out.append(
            read.model_copy(
                update={
                    "invoice_number": inv_number,
                    "invoice_type": InvoiceType(inv_type) if inv_type else None,
                }
            )
        )
    return out


async def update_payment(db: AsyncSession, payment_id: int, payload: PaymentUpdate) -> PaymentRead:
    payment = await _get_payment_orm(db, payment_id)
    if payment is None:
        raise LookupError("Payment not found")
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
    return await _to_payment_read(db, payment)


async def delete_payment(db: AsyncSession, payment_id: int) -> None:
    """Block payment deletion until a dedicated reversal workflow exists."""
    raise PaymentDeleteError("payments cannot be deleted after creation")


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
    allow_client_virement: bool = False,
) -> None:
    """Reject manual client virements until bank reconciliation owns that workflow."""
    if invoice is None or invoice.type != InvoiceType.CLIENT:
        return
    if allow_client_virement:
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
    """Keep created payments quasi-immutable to avoid desynchronising treasury/accounting flows."""
    if payload.amount is not None and payload.amount != payment.amount:
        if (
            invoice is not None
            and invoice.type == InvoiceType.CLIENT
            and payment.method == PaymentMethod.ESPECES
        ):
            raise ValueError("cash client payments cannot change amount after creation")
        raise ValueError("payments cannot change amount after creation")

    if payload.date is not None and payload.date != payment.date:
        if (
            invoice is not None
            and invoice.type == InvoiceType.CLIENT
            and payment.method == PaymentMethod.ESPECES
        ):
            raise ValueError("cash client payments cannot change date after creation")
        raise ValueError("payments cannot change date after creation")

    if payload.method is not None and payload.method != payment.method:
        if (
            invoice is not None
            and invoice.type == InvoiceType.CLIENT
            and payment.method in (PaymentMethod.CHEQUE, PaymentMethod.ESPECES)
        ):
            raise ValueError("client cheque and cash payments cannot change method after creation")
        raise ValueError("payments cannot change method after creation")

    if payload.deposited is not None and payload.deposited != payment.deposited:
        raise ValueError("payments cannot change deposit state after creation")

    if payload.deposit_date is not None and payload.deposit_date != payment.deposit_date:
        raise ValueError("payments cannot change deposit date after creation")


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
            amount=payment.amount,
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
