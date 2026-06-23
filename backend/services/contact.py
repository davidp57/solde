"""Contact service — CRUD and search."""

import calendar
import unicodedata
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.app_settings import AppSettings
from backend.models.cash import CashRegister
from backend.models.contact import Contact, ContactType
from backend.models.contact_email import ContactEmail
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment
from backend.models.salary import Salary
from backend.schemas.contact import (
    ContactCreate,
    ContactEmailImportResult,
    ContactEmailImportRow,
    ContactHistory,
    ContactInvoiceSummary,
    ContactPaymentSummary,
    ContactRead,
    ContactUpdate,
    MergeContactResult,
)


async def create_contact(db: AsyncSession, payload: ContactCreate) -> Contact:
    data = payload.model_dump(exclude={"emails"})
    contact = Contact(**data)
    db.add(contact)
    await db.flush()
    if payload.emails:
        for idx, email_item in enumerate(payload.emails):
            db.add(
                ContactEmail(
                    contact_id=contact.id,
                    email=email_item.email,
                    label=email_item.label,
                    sort_order=idx,
                )
            )
    await db.flush()
    result = await db.execute(
        select(Contact).where(Contact.id == contact.id).options(selectinload(Contact.emails))
    )
    return result.scalar_one()


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
                Contact.child_first_name.ilike(term),
                Contact.child_last_name.ilike(term),
                Contact.other_parent_first_name.ilike(term),
                Contact.other_parent_last_name.ilike(term),
            )
        )
    query = query.order_by(Contact.nom, Contact.prenom).offset(skip)
    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_contacts(
    db: AsyncSession,
    *,
    type: ContactType | None = None,
    search: str | None = None,
    active_only: bool = True,
) -> int:
    """Count contacts matching filters (no limit)."""
    query = select(func.count()).select_from(Contact)
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
                Contact.child_first_name.ilike(term),
                Contact.child_last_name.ilike(term),
                Contact.other_parent_first_name.ilike(term),
                Contact.other_parent_last_name.ilike(term),
            )
        )
    result = await db.execute(query)
    return result.scalar_one()


async def list_contacts_enriched(
    db: AsyncSession,
    *,
    type: ContactType | None = None,
    search: str | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[ContactRead]:
    """List contacts with last_invoice_ref and last_invoice_date enriched."""
    contacts = await list_contacts(
        db, type=type, search=search, active_only=active_only, skip=skip, limit=limit
    )
    if not contacts:
        return []

    contact_ids = [c.id for c in contacts]

    # Subquery: latest invoice date per contact
    latest_date_subq = (
        select(Invoice.contact_id, func.max(Invoice.date).label("max_date"))
        .where(Invoice.contact_id.in_(contact_ids))
        .group_by(Invoice.contact_id)
        .subquery()
    )

    # Join to retrieve the invoice number for that max date
    inv_result = await db.execute(
        select(Invoice.contact_id, Invoice.number, Invoice.date).join(
            latest_date_subq,
            and_(
                Invoice.contact_id == latest_date_subq.c.contact_id,
                Invoice.date == latest_date_subq.c.max_date,
            ),
        )
    )
    last_inv_by_contact: dict[int, tuple[str, date]] = {
        row.contact_id: (row.number, row.date) for row in inv_result.all()
    }

    result_list: list[ContactRead] = []
    for c in contacts:
        last = last_inv_by_contact.get(c.id)
        read = ContactRead.model_validate(c)
        read = read.model_copy(
            update={
                "last_invoice_ref": last[0] if last else None,
                "last_invoice_date": last[1] if last else None,
            }
        )
        result_list.append(read)
    return result_list


async def update_contact(db: AsyncSession, contact: Contact, payload: ContactUpdate) -> Contact:
    emails_payload = payload.emails  # None = don't touch; [] = remove all; [x...] = replace
    for field, value in payload.model_dump(exclude_unset=True, exclude={"emails"}).items():
        setattr(contact, field, value)
    if emails_payload is not None:
        from sqlalchemy import delete

        await db.execute(delete(ContactEmail).where(ContactEmail.contact_id == contact.id))
        for idx, email_item in enumerate(emails_payload):
            db.add(
                ContactEmail(
                    contact_id=contact.id,
                    email=email_item.email,
                    label=email_item.label,
                    sort_order=idx,
                )
            )
    await db.flush()
    result = await db.execute(
        select(Contact).where(Contact.id == contact.id).options(selectinload(Contact.emails))
    )
    return result.scalar_one()


async def delete_contact(db: AsyncSession, contact: Contact) -> None:
    """Soft-delete: mark as inactive rather than removing the row."""
    contact.is_active = False
    await db.flush()


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
            total_amount=inv.total_amount,
            paid_amount=inv.paid_amount,
            balance_due=inv.total_amount - inv.paid_amount,
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

    total_invoiced = sum((inv.total_amount for inv in invoices_raw), Decimal("0"))
    total_paid_inv = sum((inv.paid_amount for inv in invoices_raw), Decimal("0"))

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
    await db.flush()
    await db.refresh(debit_entry)
    await db.refresh(credit_entry)
    return debit_entry, credit_entry


def _normalize_name(name: str) -> str:
    """Normalize a name for fuzzy matching: lowercase, strip accents, collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", name.lower().strip())
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(no_accents.split())


async def import_emails_from_rows(
    db: AsyncSession,
    rows: list[ContactEmailImportRow],
) -> ContactEmailImportResult:
    """Bulk-enrich contacts with email addresses matched by name."""
    result = await db.execute(
        select(Contact).where(Contact.is_active == True).order_by(Contact.id)  # noqa: E712
    )
    all_contacts = list(result.scalars().all())

    # Build lookup: normalized name → list of contacts.
    # Keys with multiple matches are ambiguous and will be skipped to avoid
    # updating the wrong contact.
    contact_by_key: dict[str, list[Contact]] = {}
    for contact in all_contacts:
        keys = {_normalize_name(contact.nom)}
        if contact.prenom:
            full = f"{contact.nom} {contact.prenom}"
            reversed_full = f"{contact.prenom} {contact.nom}"
            keys.add(_normalize_name(full))
            keys.add(_normalize_name(reversed_full))
        for key in keys:
            contact_by_key.setdefault(key, []).append(contact)

    updated = 0
    not_found = 0
    already_has_email = 0
    updated_indices: list[int] = []
    not_found_indices: list[int] = []
    already_has_email_indices: list[int] = []

    for i, row in enumerate(rows):
        key = _normalize_name(row.nom)
        matches = contact_by_key.get(key, [])
        if len(matches) != 1:
            not_found += 1
            not_found_indices.append(i)
            continue
        found = matches[0]
        if found.email:
            already_has_email += 1
            already_has_email_indices.append(i)
            continue
        found.email = row.email
        updated += 1
        updated_indices.append(i)

    if updated > 0:
        await db.flush()

    return ContactEmailImportResult(
        rows_processed=len(rows),
        updated=updated,
        not_found=not_found,
        already_has_email=already_has_email,
        updated_indices=updated_indices,
        not_found_indices=not_found_indices,
        already_has_email_indices=already_has_email_indices,
    )


async def merge_contacts(
    db: AsyncSession,
    source_id: int,
    target_id: int,
) -> MergeContactResult:
    """Merge source contact into target contact.

    Reassigns all FK references (invoices, payments, cash, salaries) from source
    to target, copies optional fields that are empty on target, then soft-deletes
    the source contact.

    Raises ValueError if source or target does not exist, or if they are the same.
    """
    if source_id == target_id:
        raise ValueError("source_id and target_id must be different")

    source_result = await db.execute(
        select(Contact).where(Contact.id == source_id).options(selectinload(Contact.emails))
    )
    source = source_result.scalar_one_or_none()
    target_result = await db.execute(
        select(Contact).where(Contact.id == target_id).options(selectinload(Contact.emails))
    )
    target = target_result.scalar_one_or_none()
    if source is None:
        raise ValueError(f"Source contact {source_id} not found")
    if target is None:
        raise ValueError(f"Target contact {target_id} not found")

    # Reassign invoices
    invoices_result = await db.execute(
        update(Invoice).where(Invoice.contact_id == source_id).values(contact_id=target_id)
    )
    invoices_reassigned: int = invoices_result.rowcount  # type: ignore[attr-defined]

    # Reassign payments
    payments_result = await db.execute(
        update(Payment).where(Payment.contact_id == source_id).values(contact_id=target_id)
    )
    payments_reassigned: int = payments_result.rowcount  # type: ignore[attr-defined]

    # Reassign cash entries (contact_id is nullable)
    cash_result = await db.execute(
        update(CashRegister)
        .where(CashRegister.contact_id == source_id)
        .values(contact_id=target_id)
    )
    cash_reassigned: int = cash_result.rowcount  # type: ignore[attr-defined]

    # Reassign salaries (employee_id FK)
    salaries_result = await db.execute(
        update(Salary).where(Salary.employee_id == source_id).values(employee_id=target_id)
    )
    salaries_reassigned: int = salaries_result.rowcount  # type: ignore[attr-defined]

    # Copy optional text fields from source to target when target is empty
    for field in ("adresse", "telephone", "email", "notes"):
        if not getattr(target, field) and getattr(source, field):
            setattr(target, field, getattr(source, field))

    # Merge additional email addresses with deduplication.
    existing_emails = {
        target.email.strip().lower() for _ in [0] if target.email and target.email.strip()
    }
    existing_emails.update(
        email.email.strip().lower()
        for email in target.emails
        if email.email and email.email.strip()
    )
    next_sort_order = max((email.sort_order for email in target.emails), default=-1) + 1
    for source_email in list(source.emails):
        normalized = source_email.email.strip().lower()
        if not normalized or normalized in existing_emails:
            await db.delete(source_email)
            continue
        source_email.contact_id = target_id
        source_email.sort_order = next_sort_order
        next_sort_order += 1
        existing_emails.add(normalized)

    # Soft-delete source contact
    source.is_active = False

    await db.flush()

    return MergeContactResult(
        target_id=target_id,
        invoices_reassigned=invoices_reassigned,
        payments_reassigned=payments_reassigned,
        cash_entries_reassigned=cash_reassigned,
        salaries_reassigned=salaries_reassigned,
    )


# ---------------------------------------------------------------------------
# Member mailing (Lot ML)
# ---------------------------------------------------------------------------

_MEMBER_TYPES = (ContactType.CLIENT, ContactType.LES_DEUX)


def _months_ago(reference: date, months: int) -> date:
    """Return the date `months` calendar months before `reference` (clamped day)."""
    total = reference.month - 1 - months
    year = reference.year + total // 12
    month = total % 12 + 1
    day = min(reference.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _resolve_addresses(contact: Contact) -> list[str]:
    """Ordered, de-duplicated email addresses of a contact (primary first)."""
    addresses: list[str] = []
    if contact.email:
        addresses.append(contact.email)
    for extra in contact.emails:
        if extra.email and extra.email not in addresses:
            addresses.append(extra.email)
    return addresses


def _apply_placeholders(text: str, contact: Contact) -> str:
    return text.replace("{prenom}", contact.prenom or "").replace("{nom}", contact.nom or "")


async def list_active_clients(db: AsyncSession, months: int) -> list[dict[str, object]]:
    """List client members active within the last `months`.

    "Active" = at least one client invoice issued OR one payment received since
    the cutoff. Only contacts of type client/les_deux that are active and have at
    least one email address are returned. ``last_activity`` is
    ``max(last client invoice date, last payment date)`` (non-null by construction).
    """
    if months < 1:
        raise ValueError("months must be >= 1")
    cutoff = _months_ago(date.today(), months)

    last_invoice = (
        select(func.max(Invoice.date))
        .where(Invoice.contact_id == Contact.id, Invoice.type == InvoiceType.CLIENT)
        .correlate(Contact)
        .scalar_subquery()
    )
    last_payment = (
        select(func.max(Payment.date))
        .where(Payment.contact_id == Contact.id)
        .correlate(Contact)
        .scalar_subquery()
    )
    has_recent_invoice = (
        select(Invoice.id)
        .where(
            Invoice.contact_id == Contact.id,
            Invoice.type == InvoiceType.CLIENT,
            Invoice.date >= cutoff,
        )
        .correlate(Contact)
        .exists()
    )
    has_recent_payment = (
        select(Payment.id)
        .where(Payment.contact_id == Contact.id, Payment.date >= cutoff)
        .correlate(Contact)
        .exists()
    )
    has_email = or_(
        and_(Contact.email.is_not(None), Contact.email != ""),
        Contact.emails.any(),
    )

    query = (
        select(Contact, last_invoice.label("last_inv"), last_payment.label("last_pay"))
        .options(selectinload(Contact.emails))
        .where(
            Contact.type.in_(_MEMBER_TYPES),
            Contact.is_active == True,  # noqa: E712
            has_email,
            or_(has_recent_invoice, has_recent_payment),
        )
        .order_by(Contact.nom, Contact.prenom)
    )
    result = await db.execute(query)
    clients: list[dict[str, object]] = []
    for contact, last_inv, last_pay in result.all():
        activity = max((d for d in (last_inv, last_pay) if d is not None), default=None)
        addresses = _resolve_addresses(contact)
        clients.append(
            {
                "id": contact.id,
                "nom": contact.nom,
                "prenom": contact.prenom,
                "email": addresses[0] if addresses else None,
                "last_activity": activity,
            }
        )
    return clients


async def send_member_mailing(
    db: AsyncSession,
    *,
    contact_ids: list[int],
    subject: str,
    body: str,
    settings: AppSettings,
) -> dict[str, object]:
    """Send an individual email to each selected contact over one SMTP connection.

    ``To`` = primary address, secondary addresses in ``Cc``. ``{prenom}``/``{nom}``
    placeholders are substituted. Returns ``{"sent": int, "failed": [...]}``.
    Raises email_service.EmailConfigError / EmailSendError on configuration or
    connection failure.
    """
    from backend.services import email_service  # noqa: PLC0415

    result = await db.execute(
        select(Contact).options(selectinload(Contact.emails)).where(Contact.id.in_(contact_ids))
    )
    contacts = list(result.scalars().all())

    messages: list[email_service.BulkEmailMessage] = []
    failed: list[dict[str, object]] = []
    for contact in contacts:
        addresses = _resolve_addresses(contact)
        if not addresses:
            failed.append({"contact_id": contact.id, "error": "Aucune adresse email"})
            continue
        messages.append(
            {
                "to": addresses[0],
                "cc": addresses[1:],
                "subject": _apply_placeholders(subject, contact),
                "body": _apply_placeholders(body, contact),
                "ref": contact.id,
            }
        )

    send_failures: list[email_service.BulkEmailFailure] = []
    if messages:
        send_failures = email_service.send_bulk_emails(
            host=settings.smtp_host or "",
            port=settings.smtp_port,
            user=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            from_email=settings.smtp_from_email or settings.smtp_user or "",
            messages=messages,
        )
    for failure in send_failures:
        failed.append({"contact_id": failure["ref"], "error": failure["error"]})

    return {"sent": len(messages) - len(send_failures), "failed": failed}
