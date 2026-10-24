"""Payment service — record payments, update invoice status, deposit tracking."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models.cash import CashEntrySource, CashMovementType
from backend.models.contact import Contact
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.payment import (
    PaymentCancelPreview,
    PaymentCreate,
    PaymentRead,
    PaymentUpdate,
)


class InvoiceNotFoundError(LookupError):
    """Raised when a payment references an invoice that does not exist."""


class PaymentDeleteError(ValueError):
    """Raised when a payment deletion is not allowed in the standard workflow."""


class PaymentCancelError(PaymentDeleteError):
    """Raised when a payment cannot be cancelled, carrying a machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


#: Refusal codes for :func:`cancel_payment`, mapped to their API message.
CANCEL_REFUSAL_MESSAGES: dict[str, str] = {
    "PAYMENT_SUPPLIER": "only client payments can be cancelled",
    "PAYMENT_DEPOSITED": "payment has already been cashed in and cannot be cancelled",
    "PAYMENT_RECONCILED": "payment is linked to a bank transaction and cannot be cancelled",
    "FISCAL_YEAR_CLOSED": "payment belongs to a closed fiscal year and cannot be cancelled",
}


def _build_payment_read(
    payment: Payment,
    invoice_number: str | None,
    invoice_type: InvoiceType | None,
    contact_name: str | None = None,
) -> PaymentRead:
    """Build a PaymentRead DTO from an ORM Payment and pre-fetched invoice metadata."""
    read = PaymentRead.model_validate(payment)
    return read.model_copy(
        update={
            "invoice_number": invoice_number,
            "invoice_type": invoice_type,
            "contact_name": contact_name,
        }
    )


async def _to_payment_read(db: AsyncSession, payment: Payment) -> PaymentRead:
    """Build a PaymentRead DTO enriched with invoice metadata."""
    result = await db.execute(
        select(Invoice.number, Invoice.type, Contact.nom, Contact.prenom)
        .join(Contact, Contact.id == Invoice.contact_id, isouter=True)
        .where(Invoice.id == payment.invoice_id)
    )
    row = result.one_or_none()
    invoice_number: str | None = row[0] if row else None
    invoice_type: InvoiceType | None = InvoiceType(row[1]) if row and row[1] else None
    contact_name: str | None = None
    if row and row[2]:
        contact_name = f"{row[2]} {row[3]}".strip() if row[3] else row[2]
    return _build_payment_read(payment, invoice_number, invoice_type, contact_name)


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
    flush_and_refresh: bool = True,
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
        flush_and_refresh=flush_and_refresh,
    )


async def create_bank_reconciled_supplier_payment(
    db: AsyncSession,
    *,
    invoice_id: int,
    amount: Decimal,
    payment_date: date,
    reference: str | None = None,
    notes: str | None = None,
    flush_and_refresh: bool = True,
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
        flush_and_refresh=flush_and_refresh,
    )


async def _create_payment(
    db: AsyncSession,
    payload: PaymentCreate,
    *,
    allow_client_virement: bool = False,
    deposited: bool | None = None,
    deposit_date: date | None = None,
    flush_and_refresh: bool = True,
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
    # Cash payments are always immediately in the till — mark as deposited on creation.
    if payload.method == PaymentMethod.ESPECES:
        payment.deposited = True
        payment.deposit_date = payload.date
    elif deposited is not None:
        payment.deposited = deposited
    if deposit_date is not None and payment.deposit_date is None:
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
    if flush_and_refresh:
        await db.flush()
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
    inconsistent_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[PaymentRead]:
    inv = aliased(Invoice)
    cnt = aliased(Contact)
    query = (
        select(Payment, inv.number, inv.type, cnt.nom, cnt.prenom)
        .join(inv, Payment.invoice_id == inv.id)
        .join(cnt, cnt.id == inv.contact_id, isouter=True)
        .where(Payment.amount > 0)
    )
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
        # Only truly free cheques: not yet in any deposit slip, not yet confirmed
        query = query.where(Payment.deposited == False).where(Payment.in_deposit == False)  # noqa: E712
    if inconsistent_only:
        # Cheques marked as deposited but missing deposit_date
        query = (
            query.where(Payment.method == PaymentMethod.CHEQUE)
            .where(
                Payment.deposited == True  # noqa: E712
            )
            .where(Payment.deposit_date.is_(None))
        )
    query = query.order_by(Payment.date.desc(), Payment.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    return [
        _build_payment_read(
            payment,
            inv_number,
            InvoiceType(inv_type) if inv_type else None,
            f"{nom} {prenom}".strip() if nom and prenom else nom,
        )
        for payment, inv_number, inv_type, nom, prenom in rows
    ]


async def count_payments(
    db: AsyncSession,
    *,
    invoice_id: int | None = None,
    invoice_type: InvoiceType | None = None,
    contact_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    undeposited_only: bool = False,
    inconsistent_only: bool = False,
) -> int:
    """Count payments matching filters (no limit)."""
    inv = aliased(Invoice)
    query = (
        select(func.count())
        .select_from(Payment)
        .join(inv, Payment.invoice_id == inv.id)
        .where(Payment.amount > 0)
    )
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
        query = query.where(Payment.deposited == False).where(Payment.in_deposit == False)  # noqa: E712
    if inconsistent_only:
        query = (
            query.where(Payment.method == PaymentMethod.CHEQUE)
            .where(Payment.deposited == True)  # noqa: E712
            .where(Payment.deposit_date.is_(None))
        )
    result = await db.execute(query)
    return result.scalar_one()


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
    await db.flush()
    await db.refresh(payment)
    return await _to_payment_read(db, payment)


async def _find_cancel_refusal(db: AsyncSession, payment: Payment) -> str | None:
    """Return the refusal code blocking cancellation, or None if it is allowed.

    Cancellation stays open as long as the money has not reached the bank account.
    Cash is the exception: it carries ``deposited=True`` from creation because it
    is in the till, not at the bank — refusing it on that basis told users their
    cash "already reached the bank account", which is plainly false, and left a
    mistyped cash receipt with no way back. A cash receipt still in the till is
    correctable; only a bank link or a closed year stops it.
    """
    from backend.models.fiscal_year import FiscalYearStatus  # noqa: PLC0415
    from backend.services.fiscal_year_service import find_fiscal_year_for_date  # noqa: PLC0415

    invoice = await _get_invoice(db, payment.invoice_id)
    if invoice is None:
        raise InvoiceNotFoundError("Invoice not found")
    if invoice.type != InvoiceType.CLIENT:
        return "PAYMENT_SUPPLIER"
    if payment.deposited and payment.method != PaymentMethod.ESPECES:
        return "PAYMENT_DEPOSITED"
    if await _has_bank_link(db, payment.id):
        return "PAYMENT_RECONCILED"
    fiscal_year = await find_fiscal_year_for_date(db, payment.date)
    if fiscal_year is not None and fiscal_year.status == FiscalYearStatus.CLOSED:
        return "FISCAL_YEAR_CLOSED"
    return None


async def _has_bank_link(db: AsyncSession, payment_id: int) -> bool:
    """Report whether a payment is tied to a bank transaction (new or legacy link)."""
    from backend.models.bank import BankTransaction, bank_transaction_payments  # noqa: PLC0415

    linked = await db.execute(
        select(func.count())
        .select_from(bank_transaction_payments)
        .where(bank_transaction_payments.c.payment_id == payment_id)
    )
    if linked.scalar_one():
        return True
    legacy = await db.execute(
        select(func.count())
        .select_from(BankTransaction)
        .where(BankTransaction.payment_id == payment_id)
    )
    return bool(legacy.scalar_one())


async def _build_cancel_preview(
    db: AsyncSession,
    payment: Payment,
    refusal: str | None,
) -> PaymentCancelPreview:
    """Describe the outcome of cancelling *payment*, including its deposit slip."""
    from backend.services import bank_service  # noqa: PLC0415

    preview = PaymentCancelPreview(
        payment_id=payment.id,
        can_cancel=refusal is None,
        reason_code=refusal,
        amount=payment.amount,
        date=payment.date,
    )
    if refusal is not None or not payment.in_deposit:
        return preview

    deposit_id = await bank_service.get_deposit_id_for_payment(db, payment.id)
    if deposit_id is None:
        return preview
    deposit = await bank_service.get_deposit(db, deposit_id)
    if deposit is None:
        return preview

    remaining = [
        pid
        for pid in await bank_service.get_deposit_payment_ids(db, deposit_id)
        if pid != payment.id
    ]
    return preview.model_copy(
        update={
            "deposit_id": deposit_id,
            "deposit_date": deposit.date,
            "deposit_total_before": deposit.total_amount,
            "deposit_total_after": deposit.total_amount - payment.amount,
            "deposit_will_be_deleted": not remaining,
        }
    )


async def preview_payment_cancellation(db: AsyncSession, payment_id: int) -> PaymentCancelPreview:
    """Return whether a payment can be cancelled and what cancelling it would touch."""
    payment = await _get_payment_orm(db, payment_id)
    if payment is None:
        raise LookupError("Payment not found")
    refusal = await _find_cancel_refusal(db, payment)
    return await _build_cancel_preview(db, payment, refusal)


async def _detach_from_deposit(db: AsyncSession, payment: Payment) -> None:
    """Remove a payment from its (necessarily unconfirmed) deposit slip.

    ``update_deposit`` refuses an empty selection, so a slip left with no payment
    is cancelled instead — both helpers already free the payments they release.
    """
    from backend.schemas.bank import DepositUpdate  # noqa: PLC0415
    from backend.services import bank_service  # noqa: PLC0415

    if not payment.in_deposit:
        return
    deposit_id = await bank_service.get_deposit_id_for_payment(db, payment.id)
    if deposit_id is None:
        # Flag set without an association row — nothing to unlink, just clear it.
        payment.in_deposit = False
        payment.deposit_date = None
        return
    remaining = [
        pid
        for pid in await bank_service.get_deposit_payment_ids(db, deposit_id)
        if pid != payment.id
    ]
    if remaining:
        await bank_service.update_deposit(db, deposit_id, DepositUpdate(payment_ids=remaining))
    else:
        await bank_service.delete_deposit(db, deposit_id)


async def _delete_cash_entry_for_payment(db: AsyncSession, payment: Payment) -> None:
    """Remove the till movement a cash receipt created, and refresh the running balances.

    Leaving it behind would keep the money in the till after the receipt that
    justified it is gone — the very mismatch cancellation is meant to repair.
    """
    if payment.method != PaymentMethod.ESPECES:
        return

    from sqlalchemy import delete as sql_delete  # noqa: PLC0415

    from backend.models.cash import CashRegister  # noqa: PLC0415
    from backend.services.cash_service import recompute_cash_balances  # noqa: PLC0415

    await db.execute(sql_delete(CashRegister).where(CashRegister.payment_id == payment.id))
    await db.flush()
    await recompute_cash_balances(db)
    await db.flush()


async def cancel_payment(db: AsyncSession, payment_id: int) -> PaymentCancelPreview:
    """Cancel a client payment that has not been cashed in yet.

    Detaches it from its deposit slip, drops the accounting entries it generated,
    deletes it and refreshes the invoice status. Returns what was done, for audit.
    """
    from backend.models.accounting_entry import EntrySourceType  # noqa: PLC0415
    from backend.services.accounting_engine import delete_entries_for_source  # noqa: PLC0415

    payment = await _get_payment_orm(db, payment_id)
    if payment is None:
        raise LookupError("Payment not found")
    refusal = await _find_cancel_refusal(db, payment)
    if refusal is not None:
        raise PaymentCancelError(refusal, CANCEL_REFUSAL_MESSAGES[refusal])

    outcome = await _build_cancel_preview(db, payment, None)
    invoice_id = payment.invoice_id

    await _detach_from_deposit(db, payment)
    await _delete_cash_entry_for_payment(db, payment)
    await delete_entries_for_source(db, EntrySourceType.PAYMENT, payment_id)
    await db.delete(payment)
    await db.flush()
    await _refresh_invoice_status(db, invoice_id)
    await db.flush()
    return outcome


async def delete_payment(db: AsyncSession, payment_id: int) -> PaymentCancelPreview:
    """Alias kept for the existing DELETE route — see :func:`cancel_payment`."""
    return await cancel_payment(db, payment_id)


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


async def fix_inconsistent_deposit_date(
    db: AsyncSession, payment_id: int, deposit_date: date
) -> PaymentRead:
    """Set deposit_date on a cheque payment that has deposited=True but deposit_date=NULL.

    This corrects data produced by Excel imports that marked cheques as deposited
    without recording the deposit date.
    """
    payment = await _get_payment_orm(db, payment_id)
    if payment is None:
        raise LookupError("Payment not found")
    if payment.method != PaymentMethod.CHEQUE:
        raise ValueError("only cheque payments can be corrected with this endpoint")
    if not payment.deposited:
        raise ValueError("payment is not marked as deposited")
    if payment.deposit_date is not None:
        raise ValueError("payment already has a deposit date")
    payment.deposit_date = deposit_date
    await db.flush()
    await db.refresh(payment)
    return await _to_payment_read(db, payment)


async def _create_treasury_entries_for_payment(
    db: AsyncSession,
    payment: Payment,
    invoice: Invoice,
) -> None:
    """Mirror payment receipts/outlays into the operational treasury journals."""
    if payment.method != PaymentMethod.ESPECES:
        return

    from backend.services.cash_service import create_cash_entry_record  # noqa: PLC0415

    description = f"Règlement facture {invoice.number}"

    if invoice.type == InvoiceType.CLIENT:
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
    elif invoice.type == InvoiceType.FOURNISSEUR:
        await create_cash_entry_record(
            db,
            date=payment.date,
            amount=payment.amount,
            type=CashMovementType.OUT,
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
