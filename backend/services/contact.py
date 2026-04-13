"""Contact service — CRUD and search."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.contact import Contact, ContactType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.invoice import Invoice, InvoiceStatus
from backend.models.payment import Payment
from backend.schemas.contact import (
    ContactCreate,
    ContactHistory,
    ContactInvoiceSummary,
    ContactPaymentSummary,
    ContactRead,
    ContactUpdate,
)


async def create_contact(db: AsyncSession, payload: ContactCreate) -> Contact:
    contact = Contact(**payload.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def get_contact(db: AsyncSession, contact_id: int) -> Contact | None:
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    return result.scalar_one_or_none()


async def list_contacts(
    db: AsyncSession,
    *,
    type: ContactType | None = None,
    search: str | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[Contact]:
    query = select(Contact)
    if active_only:
        query = query.where(Contact.is_active == True)  # noqa: E712
    if type is not None:
        query = query.where(Contact.type == type)
    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                Contact.nom.ilike(term),
                Contact.prenom.ilike(term),
                Contact.email.ilike(term),
            )
        )
    query = query.order_by(Contact.nom, Contact.prenom).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_contact(db: AsyncSession, contact: Contact, payload: ContactUpdate) -> Contact:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(db: AsyncSession, contact: Contact) -> None:
    """Soft-delete: mark as inactive rather than removing the row."""
    contact.is_active = False
    await db.commit()


async def get_contact_history(db: AsyncSession, contact_id: int) -> ContactHistory | None:
    """Return the full history of a contact: invoices, payments, and balance."""
    contact = await get_contact(db, contact_id)
    if contact is None:
        return None

    # Fetch invoices
    inv_result = await db.execute(
        select(Invoice).where(Invoice.contact_id == contact_id).order_by(Invoice.date.desc())
    )
    invoices_raw = list(inv_result.scalars().all())

    # Fetch payments (with invoice number via join)
    pay_result = await db.execute(
        select(Payment, Invoice.number.label("inv_number"))
        .outerjoin(Invoice, Payment.invoice_id == Invoice.id)
        .where(Payment.contact_id == contact_id)
        .order_by(Payment.date.desc())
    )
    payments_raw = list(pay_result.all())

    invoice_summaries = [
        ContactInvoiceSummary(
            id=inv.id,
            number=inv.number,
            type=inv.type,
            date=inv.date,
            due_date=inv.due_date,
            status=inv.status,
            total_amount=Decimal(str(inv.total_amount)),
            paid_amount=Decimal(str(inv.paid_amount)),
            balance_due=Decimal(str(inv.total_amount)) - Decimal(str(inv.paid_amount)),
        )
        for inv in invoices_raw
    ]

    payment_summaries = [
        ContactPaymentSummary(
            id=row.Payment.id,
            date=row.Payment.date,
            amount=Decimal(str(row.Payment.amount)),
            method=row.Payment.method,
            invoice_number=row.inv_number,
        )
        for row in payments_raw
    ]

    total_invoiced = sum((Decimal(str(inv.total_amount)) for inv in invoices_raw), Decimal("0"))
    total_paid_inv = sum((Decimal(str(inv.paid_amount)) for inv in invoices_raw), Decimal("0"))

    contact_read = ContactRead.model_validate(contact)

    return ContactHistory(
        contact=contact_read,
        invoices=invoice_summaries,
        payments=payment_summaries,
        total_invoiced=total_invoiced,
        total_paid=total_paid_inv,
        total_due=total_invoiced - total_paid_inv,
    )


async def mark_creance_douteuse(
    db: AsyncSession,
    contact_id: int,
) -> tuple[AccountingEntry, AccountingEntry] | None:
    """Generate the 411→416 transfer entries for a client with a doubtful receivable.

    Returns the two created AccountingEntry objects, or None if the contact does
    not exist or has no outstanding balance.
    """
    contact = await get_contact(db, contact_id)
    if contact is None:
        return None

    # Sum balance due across all open invoices for this contact
    balance_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0)).where(
            Invoice.contact_id == contact_id,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIAL]),
        )
    )
    total_due: Decimal = Decimal(str(balance_result.scalar_one()))

    if total_due <= Decimal("0"):
        return None

    # Get current open fiscal year
    fy_result = await db.execute(
        select(FiscalYear.id).where(FiscalYear.status == FiscalYearStatus.OPEN).limit(1)
    )
    fiscal_year_id: int | None = fy_result.scalar_one_or_none()

    # Build entry number (sequential global count)
    count_result = await db.execute(select(func.count(AccountingEntry.id)))
    next_no = (count_result.scalar_one() or 0) + 1
    entry_date = date.today()
    label = f"Transfert créance douteuse — {contact.nom}" + (
        f" {contact.prenom}" if contact.prenom else ""
    )

    # Compte tiers: 411XXXX / 416XXXX (contact ID zero-padded to 4 digits)
    account_client = f"411{contact_id:04d}"
    account_douteux = f"416{contact_id:04d}"

    debit_entry = AccountingEntry(
        entry_number=f"{next_no:06d}",
        date=entry_date,
        account_number=account_douteux,
        label=label,
        debit=total_due,
        credit=Decimal("0"),
        fiscal_year_id=fiscal_year_id,
        source_type=EntrySourceType.MANUAL,
        source_id=contact_id,
    )
    db.add(debit_entry)
    await db.flush()

    credit_entry = AccountingEntry(
        entry_number=f"{next_no + 1:06d}",
        date=entry_date,
        account_number=account_client,
        label=label,
        debit=Decimal("0"),
        credit=total_due,
        fiscal_year_id=fiscal_year_id,
        source_type=EntrySourceType.MANUAL,
        source_id=contact_id,
    )
    db.add(credit_entry)
    await db.commit()
    await db.refresh(debit_entry)
    await db.refresh(credit_entry)
    return debit_entry, credit_entry
