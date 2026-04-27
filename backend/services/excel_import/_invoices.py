"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import._constants import _CLIENT_INVOICE_REFERENCE_RE
from backend.services.excel_import_parsing import (
    extract_supplier_invoice_reference as _extract_supplier_invoice_reference,
)
from backend.services.excel_import_parsing import (
    normalize_text as _normalize_text,
)
from backend.services.excel_import_parsing import (
    parse_str as _parse_str,
)
from backend.services.excel_import_types import (
    NormalizedEntryRow,
    NormalizedInvoiceRow,
)


def _extract_client_invoice_references(*values: Any) -> list[str]:
    references: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _parse_str(value, max_len=500)
        if not text:
            continue
        for reference in _CLIENT_INVOICE_REFERENCE_RE.findall(text):
            normalized_reference = _normalize_text(reference)
            if normalized_reference in seen:
                continue
            seen.add(normalized_reference)
            references.append(reference)
    return references


def _single_client_invoice_reference(*values: Any) -> str | None:
    references = _extract_client_invoice_references(*values)
    if len(references) != 1:
        return None
    return references[0]


def _normalize_decimal_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")).normalize(), "f")


def _client_settlement_account_from_method(method: str) -> str:
    normalized_method = _normalize_text(method)
    if normalized_method == "especes":
        return "531000"
    if normalized_method == "cheque":
        return "511200"
    return "512100"


def _supplier_settlement_account_from_method(method: str) -> str:
    if _normalize_text(method) == "especes":
        return "531000"
    return "512100"


def _is_client_invoice_entry_group(entry_rows: list[NormalizedEntryRow]) -> bool:
    has_receivable_debit = any(
        _normalize_text(entry_row.account_number).startswith("411") and entry_row.debit > 0
        for entry_row in entry_rows
    )
    has_revenue_credit = any(
        _normalize_text(entry_row.account_number).startswith(("70", "75")) and entry_row.credit > 0
        for entry_row in entry_rows
    )
    has_bank_or_cash_line = any(
        _normalize_text(entry_row.account_number).startswith(("512", "53"))
        for entry_row in entry_rows
    )
    return has_receivable_debit and has_revenue_credit and not has_bank_or_cash_line


def _matching_existing_client_invoice_reference(
    entry_rows: list[NormalizedEntryRow],
    existing_invoice_numbers: set[str],
) -> str | None:
    reference = _single_client_invoice_reference(*(entry_row.label for entry_row in entry_rows))
    if reference is None:
        return None
    if _normalize_text(reference) not in existing_invoice_numbers:
        return None
    if not _is_client_invoice_entry_group(entry_rows):
        return None
    return reference


def _client_invoice_line_type_from_account_number(account_number: str) -> Any | None:
    from backend.models.invoice import InvoiceLineType  # noqa: PLC0415

    normalized_account_number = _normalize_text(account_number)
    if normalized_account_number.startswith("706"):
        return InvoiceLineType.COURSE
    if normalized_account_number.startswith("756"):
        return InvoiceLineType.ADHESION
    if normalized_account_number.startswith("758"):
        return InvoiceLineType.OTHER
    return None


def _client_invoice_breakdown_from_entry_group(
    entry_rows: list[NormalizedEntryRow],
) -> dict[Any, Decimal] | None:
    from backend.models.invoice import InvoiceLineType  # noqa: PLC0415

    if not _is_client_invoice_entry_group(entry_rows):
        return None

    breakdown: dict[Any, Decimal] = {
        InvoiceLineType.COURSE: Decimal("0"),
        InvoiceLineType.ADHESION: Decimal("0"),
        InvoiceLineType.OTHER: Decimal("0"),
    }
    receivable_total = Decimal("0")
    revenue_total = Decimal("0")

    for entry_row in entry_rows:
        normalized_account_number = _normalize_text(entry_row.account_number)
        if normalized_account_number.startswith("411"):
            receivable_total += entry_row.debit
            continue
        if entry_row.credit <= 0:
            continue
        if normalized_account_number.startswith(("70", "75")):
            line_type = _client_invoice_line_type_from_account_number(entry_row.account_number)
            if line_type is None:
                return None
            breakdown[line_type] += entry_row.credit
            revenue_total += entry_row.credit

    if revenue_total <= 0 or receivable_total != revenue_total:
        return None

    return {line_type: amount for line_type, amount in breakdown.items() if amount != Decimal("0")}


def _current_client_invoice_breakdown(invoice: Any) -> dict[Any, Decimal]:
    from backend.models.invoice import infer_client_line_type  # noqa: PLC0415

    breakdown: dict[Any, Decimal] = {}
    for line in invoice.lines:
        line_type = line.line_type or infer_client_line_type(line.description, invoice.label)
        breakdown[line_type] = breakdown.get(line_type, Decimal("0")) + Decimal(str(line.amount))
    return {line_type: amount for line_type, amount in breakdown.items() if amount != Decimal("0")}


def _can_clarify_existing_client_invoice(invoice: Any) -> bool:
    from backend.models.invoice import InvoiceLineType, infer_client_line_type  # noqa: PLC0415

    if not invoice.lines:
        return False
    current_line_types = {
        line.line_type or infer_client_line_type(line.description, invoice.label)
        for line in invoice.lines
    }
    return current_line_types == {InvoiceLineType.OTHER}


async def _find_clarifiable_existing_client_invoice(
    db: AsyncSession,
    entry_rows: list[NormalizedEntryRow],
    existing_client_invoices_by_number: dict[str, Any] | None = None,
) -> Any | None:
    from sqlalchemy import select  # noqa: PLC0415
    from sqlalchemy.orm import selectinload  # noqa: PLC0415

    from backend.models.invoice import (  # noqa: PLC0415
        Invoice,
        InvoiceType,
    )

    reference = _single_client_invoice_reference(*(entry_row.label for entry_row in entry_rows))
    if reference is None:
        return None

    breakdown = _client_invoice_breakdown_from_entry_group(entry_rows)
    if breakdown is None:
        return None

    if existing_client_invoices_by_number is None:
        invoice_result = await db.execute(
            select(Invoice)
            .where(Invoice.type == InvoiceType.CLIENT, Invoice.number == reference)
            .options(selectinload(Invoice.lines))
        )
        invoice = invoice_result.scalar_one_or_none()
    else:
        invoice = existing_client_invoices_by_number.get(_normalize_text(reference))

    if invoice is None or not _can_clarify_existing_client_invoice(invoice):
        return None

    current_breakdown = _current_client_invoice_breakdown(invoice)
    if current_breakdown == breakdown:
        return None

    total_amount = sum(breakdown.values(), Decimal("0"))
    if total_amount != Decimal(str(invoice.total_amount)):
        return None

    return invoice


async def _clarify_existing_client_invoice_from_entries(
    db: AsyncSession,
    entry_rows: list[NormalizedEntryRow],
    existing_client_invoices_by_number: dict[str, Any] | None = None,
) -> Any | None:
    from sqlalchemy import delete  # noqa: PLC0415

    from backend.models.accounting_entry import AccountingEntry, EntrySourceType  # noqa: PLC0415
    from backend.models.invoice import (  # noqa: PLC0415
        InvoiceLabel,
        InvoiceLine,
        default_client_line_description,
        derive_client_invoice_label,
    )
    from backend.services.accounting_engine import generate_entries_for_invoice  # noqa: PLC0415

    invoice = await _find_clarifiable_existing_client_invoice(
        db,
        entry_rows,
        existing_client_invoices_by_number,
    )
    if invoice is None:
        return None

    breakdown = _client_invoice_breakdown_from_entry_group(entry_rows)
    if breakdown is None:
        return None

    await db.execute(
        delete(AccountingEntry).where(
            AccountingEntry.source_type == EntrySourceType.INVOICE,
            AccountingEntry.source_id == invoice.id,
        )
    )

    invoice.lines.clear()
    await db.flush()

    positive_line_types = {line_type for line_type, amount in breakdown.items() if amount > 0}
    invoice.label = derive_client_invoice_label(positive_line_types)
    invoice.has_explicit_breakdown = len(breakdown) > 1 or invoice.label != InvoiceLabel.GENERAL
    invoice.lines.extend(
        InvoiceLine(
            invoice_id=invoice.id,
            description=default_client_line_description(line_type),
            line_type=line_type,
            quantity=Decimal("1"),
            unit_price=amount,
            amount=amount,
        )
        for line_type, amount in sorted(breakdown.items(), key=lambda item: item[0].value)
    )

    await db.flush()
    await generate_entries_for_invoice(db, invoice)
    await db.flush()
    return invoice


async def _load_existing_client_invoices_by_number(db: AsyncSession) -> dict[str, Any]:
    from sqlalchemy import select  # noqa: PLC0415
    from sqlalchemy.orm import selectinload  # noqa: PLC0415

    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415

    result = await db.execute(
        select(Invoice)
        .where(Invoice.type == InvoiceType.CLIENT)
        .options(selectinload(Invoice.lines))
    )
    return {
        _normalize_text(invoice.number): invoice
        for invoice in result.scalars().all()
        if invoice.number
    }


def _is_client_payment_entry_group(entry_rows: list[NormalizedEntryRow]) -> bool:
    has_receivable_credit = any(
        _normalize_text(entry_row.account_number).startswith("411") and entry_row.credit > 0
        for entry_row in entry_rows
    )
    settlement_accounts = {
        _normalize_text(entry_row.account_number)
        for entry_row in entry_rows
        if entry_row.debit > 0
        and _normalize_text(entry_row.account_number).startswith(("511", "512", "53"))
    }
    has_revenue_line = any(
        _normalize_text(entry_row.account_number).startswith(("70", "75"))
        for entry_row in entry_rows
    )
    has_supplier_line = any(
        _normalize_text(entry_row.account_number).startswith("401") for entry_row in entry_rows
    )
    return (
        has_receivable_credit
        and len(settlement_accounts) == 1
        and not has_revenue_line
        and not has_supplier_line
    )


async def _load_existing_client_payment_reference_signatures(
    db: AsyncSession,
) -> set[tuple[str, str, str]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    result = await db.execute(
        select(Invoice.number, Invoice.reference, Payment.amount, Payment.method)
        .join(Payment, Payment.invoice_id == Invoice.id)
        .where(Invoice.type == InvoiceType.CLIENT)
    )

    signatures: set[tuple[str, str, str]] = set()
    for number, reference, amount, method in result.all():
        references = {number}
        if reference:
            references.add(reference)
        for client_reference in references:
            signatures.add(
                (
                    _normalize_text(client_reference),
                    _normalize_decimal_text(amount),
                    _client_settlement_account_from_method(str(method)),
                )
            )
    return signatures


def _build_client_invoice_lines_from_import_row(
    invoice_row: NormalizedInvoiceRow,
) -> list[dict[str, Any]]:
    from backend.models.invoice import (  # noqa: PLC0415
        InvoiceLabel,
        InvoiceLineType,
        default_client_line_description,
    )

    if invoice_row.course_amount is not None and invoice_row.adhesion_amount is not None:
        return [
            {
                "description": default_client_line_description(InvoiceLineType.COURSE),
                "line_type": InvoiceLineType.COURSE,
                "amount": invoice_row.course_amount,
            },
            {
                "description": default_client_line_description(InvoiceLineType.ADHESION),
                "line_type": InvoiceLineType.ADHESION,
                "amount": invoice_row.adhesion_amount,
            },
        ]

    label = InvoiceLabel(invoice_row.label)
    if label == InvoiceLabel.CS:
        line_type = InvoiceLineType.COURSE
    elif label == InvoiceLabel.ADHESION:
        line_type = InvoiceLineType.ADHESION
    else:
        line_type = InvoiceLineType.OTHER

    return [
        {
            "description": default_client_line_description(line_type),
            "line_type": line_type,
            "amount": invoice_row.amount,
        }
    ]


def _merge_existing_client_invoice_entry_groups(
    entry_groups: list[list[NormalizedEntryRow]],
    start_index: int,
    existing_invoice_numbers: set[str],
) -> tuple[list[NormalizedEntryRow], int]:
    merged_group = list(entry_groups[start_index])
    reference = _matching_existing_client_invoice_reference(merged_group, existing_invoice_numbers)
    if reference is None:
        return merged_group, start_index + 1

    next_index = start_index + 1
    while next_index < len(entry_groups):
        next_group = entry_groups[next_index]
        next_reference = _matching_existing_client_invoice_reference(
            next_group,
            existing_invoice_numbers,
        )
        if next_reference != reference:
            break
        merged_group.extend(next_group)
        next_index += 1

    return merged_group, next_index


def _matching_existing_client_payment_reference(
    entry_rows: list[NormalizedEntryRow],
    existing_client_payment_signatures: set[tuple[str, str, str]],
) -> str | None:
    reference = _single_client_invoice_reference(*(entry_row.label for entry_row in entry_rows))
    if reference is None:
        return None
    if not _is_client_payment_entry_group(entry_rows):
        return None

    settlement_accounts = {
        _normalize_text(entry_row.account_number)
        for entry_row in entry_rows
        if entry_row.debit > 0
        and _normalize_text(entry_row.account_number).startswith(("511", "512", "53"))
    }
    if len(settlement_accounts) != 1:
        return None

    amount = sum(
        (
            entry_row.debit
            for entry_row in entry_rows
            if entry_row.debit > 0
            and _normalize_text(entry_row.account_number).startswith(("511", "512", "53"))
        ),
        start=Decimal("0"),
    )
    if amount <= 0:
        return None

    signature = (
        _normalize_text(reference),
        _normalize_decimal_text(amount),
        next(iter(settlement_accounts)),
    )
    if signature not in existing_client_payment_signatures:
        return None
    return reference


def _is_supplier_direct_settlement_entry_group(entry_rows: list[NormalizedEntryRow]) -> bool:
    has_expense_debit = any(
        _normalize_text(entry_row.account_number).startswith(("6", "60", "61", "62"))
        and entry_row.debit > 0
        for entry_row in entry_rows
    )
    settlement_accounts = {
        _normalize_text(entry_row.account_number)
        for entry_row in entry_rows
        if entry_row.credit > 0
        and _normalize_text(entry_row.account_number).startswith(("512", "53"))
    }
    has_supplier_account = any(
        _normalize_text(entry_row.account_number).startswith("401") for entry_row in entry_rows
    )
    return has_expense_debit and len(settlement_accounts) == 1 and not has_supplier_account


async def _load_existing_supplier_payment_reference_signatures(
    db: AsyncSession,
) -> set[tuple[str, str, str, str]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    result = await db.execute(
        select(Invoice.number, Invoice.reference, Payment.date, Payment.amount, Payment.method)
        .join(Payment, Payment.invoice_id == Invoice.id)
        .where(Invoice.type == InvoiceType.FOURNISSEUR)
    )
    signatures: set[tuple[str, str, str, str]] = set()
    for number, reference, payment_date, amount, method in result.all():
        supplier_reference = reference or number
        if not supplier_reference:
            continue
        signatures.add(
            (
                _normalize_text(supplier_reference),
                payment_date.isoformat(),
                _normalize_decimal_text(amount),
                _supplier_settlement_account_from_method(str(method)),
            )
        )
    return signatures


def _matching_existing_supplier_invoice_payment_reference(
    entry_rows: list[NormalizedEntryRow],
    existing_supplier_payment_signatures: set[tuple[str, str, str, str]],
) -> str | None:
    reference = _extract_supplier_invoice_reference(*(entry_row.label for entry_row in entry_rows))
    if reference is None:
        return None
    if not _is_supplier_direct_settlement_entry_group(entry_rows):
        return None

    dates = {entry_row.entry_date for entry_row in entry_rows}
    if len(dates) != 1:
        return None

    amount = sum((entry_row.debit for entry_row in entry_rows), start=Decimal("0"))
    settlement_accounts = {
        _normalize_text(entry_row.account_number)
        for entry_row in entry_rows
        if entry_row.credit > 0
        and _normalize_text(entry_row.account_number).startswith(("512", "53"))
    }
    if len(settlement_accounts) != 1 or amount <= 0:
        return None

    signature = (
        _normalize_text(reference),
        next(iter(dates)).isoformat(),
        _normalize_decimal_text(amount),
        next(iter(settlement_accounts)),
    )
    if signature not in existing_supplier_payment_signatures:
        return None
    return reference
