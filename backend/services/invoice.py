"""Invoice service — CRUD, numbering, status changes, duplication."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.invoice import (
    Invoice,
    InvoiceLabel,
    InvoiceLine,
    InvoiceLineType,
    InvoiceStatus,
    InvoiceType,
    derive_client_invoice_label,
    infer_client_line_type,
)
from backend.schemas.invoice import InvoiceCreate, InvoiceLineCreate, InvoiceUpdate
from backend.services import settings as settings_service


class InvoiceStatusError(Exception):
    """Raised when an invalid status transition is attempted."""


class InvoiceDeleteError(Exception):
    """Raised when a non-draft invoice is deleted."""


class InvoiceUpdateError(Exception):
    """Raised when an invoice cannot be edited in its current business state."""


# Valid transitions: from → set of allowed target statuses
_VALID_TRANSITIONS: dict[InvoiceStatus, set[InvoiceStatus]] = {
    InvoiceStatus.DRAFT: {
        InvoiceStatus.SENT,
        InvoiceStatus.PAID,
        InvoiceStatus.PARTIAL,
        InvoiceStatus.OVERDUE,
        InvoiceStatus.DISPUTED,
    },
    InvoiceStatus.SENT: {
        InvoiceStatus.PAID,
        InvoiceStatus.PARTIAL,
        InvoiceStatus.OVERDUE,
        InvoiceStatus.DISPUTED,
    },
    InvoiceStatus.PARTIAL: {
        InvoiceStatus.PAID,
        InvoiceStatus.OVERDUE,
        InvoiceStatus.DISPUTED,
    },
    InvoiceStatus.OVERDUE: {
        InvoiceStatus.PAID,
        InvoiceStatus.PARTIAL,
        InvoiceStatus.DISPUTED,
    },
    InvoiceStatus.DISPUTED: {
        InvoiceStatus.PAID,
        InvoiceStatus.PARTIAL,
        InvoiceStatus.OVERDUE,
    },
    InvoiceStatus.PAID: set(),  # final state
}


def _compute_line_amount(quantity: Decimal, unit_price: Decimal) -> Decimal:
    return (quantity * unit_price).quantize(Decimal("0.01"))


def _compute_total(lines: list[InvoiceLineCreate]) -> Decimal:
    return sum(
        (_compute_line_amount(ln.quantity, ln.unit_price) for ln in lines),
        Decimal("0"),
    )


def _resolve_client_line_type(
    description: str,
    line_type: InvoiceLineType | None,
    fallback_label: InvoiceLabel | None,
) -> InvoiceLineType:
    return line_type or infer_client_line_type(description, fallback_label)


def _derive_client_label(
    lines: Sequence[InvoiceLineCreate | InvoiceLine],
    fallback_label: InvoiceLabel | None,
) -> InvoiceLabel:
    line_types = {
        _resolve_client_line_type(
            line.description,
            getattr(line, "line_type", None),
            fallback_label,
        )
        for line in lines
    }
    return derive_client_invoice_label(line_types)


def _resolve_invoice_label(
    invoice_type: InvoiceType,
    payload_label: InvoiceLabel | None,
    lines: Sequence[InvoiceLineCreate | InvoiceLine],
) -> InvoiceLabel | None:
    if invoice_type != InvoiceType.CLIENT or not lines:
        return payload_label
    return _derive_client_label(lines, payload_label)


def _has_user_entered_breakdown(
    invoice_type: InvoiceType,
    line_count: int,
) -> bool:
    return invoice_type == InvoiceType.CLIENT and line_count >= 2


def apply_default_due_date(
    invoice_date: date,
    due_date: date | None,
    default_invoice_due_days: int | None,
) -> date | None:
    if due_date is not None or default_invoice_due_days is None:
        return due_date
    return invoice_date + timedelta(days=default_invoice_due_days)


async def _next_number(db: AsyncSession, invoice_type: InvoiceType, year: int) -> str:
    """Generate the next sequential invoice number for a given type and year.

    Format: YYYY-C-NNNN for client, YYYY-F-NNNN for supplier.
    """
    prefix = "C" if invoice_type == InvoiceType.CLIENT else "F"
    pattern = f"{year}-{prefix}-%"
    result = await db.execute(
        select(Invoice.number)
        .where(Invoice.number.like(pattern))
        .order_by(Invoice.id.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    seq = 1 if last is None else int(last.split("-")[-1]) + 1
    return f"{year}-{prefix}-{seq:04d}"


async def create_invoice(db: AsyncSession, payload: InvoiceCreate) -> Invoice:
    """Create an invoice with auto-generated number and computed total."""
    year = payload.date.year
    number = await _next_number(db, payload.type, year)
    resolved_due_date = apply_default_due_date(
        payload.date,
        payload.due_date,
        await settings_service.get_default_invoice_due_days(db),
    )

    # Compute total
    if payload.lines:
        total = _compute_total(payload.lines)
    elif payload.total_amount is not None:
        total = payload.total_amount
    else:
        total = Decimal("0")

    resolved_label = _resolve_invoice_label(payload.type, payload.label, payload.lines)

    invoice = Invoice(
        number=number,
        type=payload.type,
        contact_id=payload.contact_id,
        date=payload.date,
        due_date=resolved_due_date,
        label=resolved_label,
        description=payload.description,
        reference=payload.reference,
        total_amount=total,
        paid_amount=Decimal("0"),
        has_explicit_breakdown=_has_user_entered_breakdown(
            payload.type,
            len(payload.lines),
        ),
        status=InvoiceStatus.DRAFT,
    )
    db.add(invoice)
    await db.flush()  # get invoice.id before adding lines

    for ln in payload.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            description=ln.description,
            line_type=(
                _resolve_client_line_type(ln.description, ln.line_type, resolved_label)
                if payload.type == InvoiceType.CLIENT
                else None
            ),
            quantity=ln.quantity,
            unit_price=ln.unit_price,
            amount=_compute_line_amount(ln.quantity, ln.unit_price),
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)
    return await get_invoice(db, invoice.id)  # type: ignore[return-value]


async def get_invoice(db: AsyncSession, invoice_id: int) -> Invoice | None:
    """Get an invoice by ID, with lines eagerly loaded."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id).options(selectinload(Invoice.lines))
    )
    return result.scalar_one_or_none()


async def list_invoices(
    db: AsyncSession,
    *,
    invoice_type: InvoiceType | None = None,
    status: InvoiceStatus | None = None,
    contact_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    year: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Invoice]:
    """List invoices with optional filters."""
    query = select(Invoice).options(selectinload(Invoice.lines))
    if invoice_type is not None:
        query = query.where(Invoice.type == invoice_type)
    if status is not None:
        query = query.where(Invoice.status == status)
    if contact_id is not None:
        query = query.where(Invoice.contact_id == contact_id)
    if from_date is not None:
        query = query.where(Invoice.date >= from_date)
    if to_date is not None:
        query = query.where(Invoice.date <= to_date)
    if year is not None:
        query = query.where(extract("year", Invoice.date) == year)
    query = query.order_by(Invoice.date.desc(), Invoice.id.desc()).offset(skip)
    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_invoice(db: AsyncSession, invoice: Invoice, payload: InvoiceUpdate) -> Invoice:
    """Update invoice fields. Recalculates total if lines are provided."""
    refreshed_invoice = await get_invoice(db, invoice.id)
    if refreshed_invoice is None:
        raise InvoiceUpdateError("Invoice not found")
    invoice = refreshed_invoice

    if invoice.status != InvoiceStatus.DRAFT and not (
        invoice.status == InvoiceStatus.SENT and invoice.paid_amount == Decimal("0")
    ):
        raise InvoiceUpdateError(f"Invoice in status '{invoice.status}' cannot be edited")

    should_regenerate_entries = invoice.status == InvoiceStatus.SENT
    if should_regenerate_entries:
        await db.execute(
            delete(AccountingEntry).where(
                AccountingEntry.source_type == EntrySourceType.INVOICE,
                AccountingEntry.source_id == invoice.id,
            )
        )

    for field in (
        "contact_id",
        "date",
        "due_date",
        "description",
        "reference",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(invoice, field, value)

    if payload.label is not None and invoice.type != InvoiceType.CLIENT:
        invoice.label = payload.label

    effective_lines: Sequence[InvoiceLineCreate | InvoiceLine] = invoice.lines
    if payload.lines is not None:
        # Replace all existing lines
        for existing_line in list(invoice.lines):
            await db.delete(existing_line)
        await db.flush()
        new_lines = []
        resolved_label = _resolve_invoice_label(
            invoice.type,
            payload.label if payload.label is not None else invoice.label,
            payload.lines,
        )
        for ln in payload.lines:
            line = InvoiceLine(
                invoice_id=invoice.id,
                description=ln.description,
                line_type=(
                    _resolve_client_line_type(ln.description, ln.line_type, resolved_label)
                    if invoice.type == InvoiceType.CLIENT
                    else None
                ),
                quantity=ln.quantity,
                unit_price=ln.unit_price,
                amount=_compute_line_amount(ln.quantity, ln.unit_price),
            )
            db.add(line)
            new_lines.append(line)
        invoice.total_amount = _compute_total(payload.lines)
        effective_lines = payload.lines
    elif payload.total_amount is not None:
        invoice.total_amount = payload.total_amount

    invoice.label = _resolve_invoice_label(
        invoice.type,
        payload.label if payload.label is not None else invoice.label,
        effective_lines,
    )

    line_count = len(payload.lines) if payload.lines is not None else len(invoice.lines)
    invoice.has_explicit_breakdown = _has_user_entered_breakdown(
        invoice.type,
        line_count,
    )

    invoice.updated_at = datetime.now(UTC)
    if should_regenerate_entries:
        from backend.services.accounting_engine import generate_entries_for_invoice  # noqa: PLC0415

        await db.flush()
        await generate_entries_for_invoice(db, invoice)
    invoice_id = invoice.id  # save before expire clears attributes
    await db.commit()
    db.expire(invoice)  # force selectinload to re-query lines from DB
    return await get_invoice(db, invoice_id)  # type: ignore[return-value]


async def update_invoice_status(
    db: AsyncSession, invoice: Invoice, new_status: InvoiceStatus
) -> Invoice:
    """Change the status of an invoice, enforcing valid transitions."""
    allowed = _VALID_TRANSITIONS.get(invoice.status, set())
    if new_status not in allowed:
        raise InvoiceStatusError(f"Cannot transition from '{invoice.status}' to '{new_status}'")
    invoice.status = new_status
    invoice.updated_at = datetime.now(UTC)
    if new_status == InvoiceStatus.SENT:
        from backend.services.accounting_engine import (
            generate_entries_for_invoice,
        )  # noqa: PLC0415

        await generate_entries_for_invoice(db, invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


async def duplicate_invoice(db: AsyncSession, source: Invoice) -> Invoice:
    """Create a new draft invoice by copying the source, with a new number and today's date."""
    today = date.today()
    number = await _next_number(db, source.type, today.year)

    copy = Invoice(
        number=number,
        type=source.type,
        contact_id=source.contact_id,
        date=today,
        due_date=None,
        label=_resolve_invoice_label(source.type, source.label, source.lines),
        description=source.description,
        reference=None,
        total_amount=source.total_amount,
        paid_amount=Decimal("0"),
        has_explicit_breakdown=_has_user_entered_breakdown(
            source.type,
            len(source.lines),
        ),
        status=InvoiceStatus.DRAFT,
    )
    db.add(copy)
    await db.flush()

    for src_line in source.lines:
        line = InvoiceLine(
            invoice_id=copy.id,
            description=src_line.description,
            line_type=src_line.line_type,
            quantity=src_line.quantity,
            unit_price=src_line.unit_price,
            amount=src_line.amount,
        )
        db.add(line)

    await db.commit()
    return await get_invoice(db, copy.id)  # type: ignore[return-value]


async def delete_invoice(db: AsyncSession, invoice: Invoice) -> None:
    """Permanently delete an invoice. Only draft invoices may be deleted."""
    if invoice.status != InvoiceStatus.DRAFT:
        raise InvoiceDeleteError("Only draft invoices can be deleted")
    await db.delete(invoice)
    await db.commit()


async def set_pdf_path(db: AsyncSession, invoice: Invoice, pdf_path: str) -> Invoice:
    """Update the pdf_path field after PDF generation."""
    invoice.pdf_path = pdf_path
    await db.commit()
    await db.refresh(invoice)
    return invoice


async def set_file_path(db: AsyncSession, invoice: Invoice, file_path: str) -> Invoice:
    """Update the file_path field after a supplier file upload."""
    invoice.file_path = file_path
    await db.commit()
    await db.refresh(invoice)
    return invoice
