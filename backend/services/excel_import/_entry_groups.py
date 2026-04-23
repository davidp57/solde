"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import._constants import _SupplierInvoiceCandidate
from backend.services.excel_import._invoices import _single_client_invoice_reference
from backend.services.excel_import._loaders import (
    _payment_row_from_bank_row,
    _payment_signature,
)
from backend.services.excel_import._salary import (
    _entry_group_amount_signature,
    _extract_salary_month,
    _is_salary_accrual_like_entry_group,
    _is_salary_payment_like_entry_group,
    _is_salary_related_label,
)
from backend.services.excel_import_parsing import (
    extract_supplier_invoice_reference as _extract_supplier_invoice_reference,
)
from backend.services.excel_import_parsing import (
    infer_supplier_contact_name as _infer_supplier_contact_name,
)
from backend.services.excel_import_parsing import (
    is_supplier_subcontracting_description as _is_supplier_subcontracting_description,
)
from backend.services.excel_import_parsing import (
    normalize_text as _normalize_text,
)
from backend.services.excel_import_parsing import (
    strip_supplier_invoice_reference as _strip_supplier_invoice_reference,
)
from backend.services.excel_import_payment_matching import (
    resolve_payment_match_with_database as _resolve_payment_match,
)
from backend.services.excel_import_policy import (
    format_row_issue,
    make_payment_resolution_issue,
    resolve_invoice_contact_match,
)
from backend.services.excel_import_results import ImportResult
from backend.services.excel_import_state import (
    accounting_entry_group_signature as _accounting_entry_group_signature,
)
from backend.services.excel_import_state import (
    accounting_entry_line_signature as _accounting_entry_line_signature,
)
from backend.services.excel_import_types import (
    NormalizedBankRow,
    NormalizedCashRow,
    NormalizedEntryRow,
    NormalizedInvoiceRow,
)
from backend.services.invoice import apply_default_due_date


def _matching_existing_salary_entry_group(
    entry_rows: list[NormalizedEntryRow],
    existing_salary_group_signatures: dict[str, set[tuple[str, ...]]],
) -> str | None:
    month = _extract_salary_month(*(entry_row.label for entry_row in entry_rows))
    if month is None:
        return None
    normalized_labels = [_normalize_text(entry_row.label) for entry_row in entry_rows]
    if not any(_is_salary_related_label(label) for label in normalized_labels):
        return None
    month_signatures = existing_salary_group_signatures.get(month)
    if month_signatures is None:
        return None
    if _entry_group_amount_signature(entry_rows) in month_signatures:
        return month
    if _is_salary_accrual_like_entry_group(entry_rows):
        return month
    if _is_salary_payment_like_entry_group(entry_rows):
        return month
    return None


def _supplier_invoice_candidate_from_bank_row(
    row: NormalizedBankRow,
) -> _SupplierInvoiceCandidate | None:
    if row.amount >= 0:
        return None
    invoice_number = _extract_supplier_invoice_reference(row.description, row.reference)
    if not invoice_number:
        return None
    description = _strip_supplier_invoice_reference(row.description) or invoice_number
    contact_name = _infer_supplier_contact_name(description) or description
    label = "cs" if _is_supplier_subcontracting_description(description) else "general"
    return _SupplierInvoiceCandidate(
        source_row_number=row.source_row_number,
        invoice_date=row.entry_date,
        amount=abs(row.amount),
        invoice_number=invoice_number,
        contact_name=contact_name,
        description=description,
        label=label,
        payment_method="virement",
    )


def _supplier_invoice_candidate_from_cash_row(
    row: NormalizedCashRow,
) -> _SupplierInvoiceCandidate | None:
    if row.movement_type != "out":
        return None
    invoice_number = _extract_supplier_invoice_reference(row.reference, row.description)
    if not invoice_number:
        return None
    description = _strip_supplier_invoice_reference(row.description) or invoice_number
    contact_name = row.contact_name or _infer_supplier_contact_name(description) or description
    label = "cs" if _is_supplier_subcontracting_description(description) else "general"
    return _SupplierInvoiceCandidate(
        source_row_number=row.source_row_number,
        invoice_date=row.entry_date,
        amount=row.amount,
        invoice_number=invoice_number,
        contact_name=contact_name,
        description=description,
        label=label,
        payment_method="especes",
    )


def _invoice_row_from_supplier_candidate(
    candidate: _SupplierInvoiceCandidate,
) -> NormalizedInvoiceRow:
    return NormalizedInvoiceRow(
        source_row_number=candidate.source_row_number,
        invoice_date=candidate.invoice_date,
        amount=candidate.amount,
        contact_name=candidate.contact_name,
        invoice_number=candidate.invoice_number,
        label=candidate.label,
    )


def _build_entry_row_groups(
    normalized_rows: list[NormalizedEntryRow],
) -> list[list[NormalizedEntryRow]]:
    if not normalized_rows:
        return []

    if not any(entry_row.change_marker is not None for entry_row in normalized_rows):
        return [[entry_row] for entry_row in normalized_rows]

    marker_groups: list[list[NormalizedEntryRow]] = []
    current_group: list[NormalizedEntryRow] = []
    last_change_marker: str | None = None
    for entry_row in normalized_rows:
        if (
            current_group
            and entry_row.change_marker is not None
            and last_change_marker is not None
            and entry_row.change_marker != last_change_marker
        ):
            marker_groups.append(current_group)
            current_group = []

        current_group.append(entry_row)
        if entry_row.change_marker is not None:
            last_change_marker = entry_row.change_marker

    if current_group:
        marker_groups.append(current_group)

    groups: list[list[NormalizedEntryRow]] = []
    for marker_group in marker_groups:
        balance = Decimal("0")
        current_subgroup: list[NormalizedEntryRow] = []
        for index, entry_row in enumerate(marker_group):
            current_subgroup.append(entry_row)
            balance += entry_row.debit - entry_row.credit
            if balance == 0 and index < len(marker_group) - 1:
                groups.append(current_subgroup)
                current_subgroup = []
        if current_subgroup:
            groups.append(current_subgroup)

    return groups


def _normalized_entry_group_signature(
    entry_rows: list[NormalizedEntryRow],
) -> tuple[str, ...]:
    return _accounting_entry_group_signature(
        [
            _accounting_entry_line_signature(
                entry_date=entry_row.entry_date,
                account_number=entry_row.account_number,
                debit=entry_row.debit,
                credit=entry_row.credit,
            )
            for entry_row in entry_rows
        ]
    )


async def _queue_client_payment_from_bank_row(
    db: AsyncSession,
    *,
    bank_row: NormalizedBankRow,
    existing_payment_signatures: set[tuple[int, str, str, str, str]],
    created_payments: list[tuple[Any, Any]],
    affected_invoice_ids: set[int],
    result: ImportResult,
    sheet_name: str,
) -> None:
    from backend.models.invoice import InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment, PaymentMethod  # noqa: PLC0415

    if bank_row.amount <= 0:
        return

    invoice_reference = _single_client_invoice_reference(bank_row.reference, bank_row.description)
    if invoice_reference is None:
        return

    resolution = await _resolve_payment_match(
        db,
        _payment_row_from_bank_row(bank_row, invoice_reference=invoice_reference),
    )
    blocking_issue = make_payment_resolution_issue(
        source_row_number=bank_row.source_row_number,
        status=resolution.status,
        candidate=resolution.candidate,
        message=resolution.message,
        require_persistable_candidate=True,
    )
    if blocking_issue is not None:
        return

    candidate = resolution.candidate
    assert candidate is not None
    assert candidate.invoice_id is not None
    signature = _payment_signature(
        invoice_id=candidate.invoice_id,
        payment_date=bank_row.entry_date,
        amount=bank_row.amount,
        method=PaymentMethod.VIREMENT.value,
    )
    if signature in existing_payment_signatures:
        return

    payment = Payment(
        invoice_id=candidate.invoice_id,
        contact_id=candidate.contact_id,
        date=bank_row.entry_date,
        amount=bank_row.amount,
        method=PaymentMethod.VIREMENT,
        reference=invoice_reference,
        notes=bank_row.description,
        deposited=True,
        deposit_date=bank_row.entry_date,
    )
    db.add(payment)
    created_payments.append((payment, candidate.invoice_type or InvoiceType.CLIENT))
    affected_invoice_ids.add(candidate.invoice_id)
    existing_payment_signatures.add(signature)
    result.payments_created += 1
    result.add_imported_row(sheet_name, "payments")


async def _ensure_supplier_invoice_payment(
    db: AsyncSession,
    *,
    candidate: _SupplierInvoiceCandidate,
    existing_contacts_by_preview_key: dict[str, list[Any]],
    result: ImportResult,
    sheet_name: str,
    default_invoice_due_days: int | None,
) -> tuple[int, int, int | None, bool]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact, ContactType  # noqa: PLC0415
    from backend.models.invoice import (  # noqa: PLC0415
        Invoice,
        InvoiceLabel,
        InvoiceStatus,
        InvoiceType,
    )
    from backend.models.payment import Payment, PaymentMethod  # noqa: PLC0415

    invoice_result = await db.execute(
        select(Invoice).where(Invoice.number == candidate.invoice_number)
    )
    invoice = invoice_result.scalar_one_or_none()
    created_invoice = False
    if invoice is None:
        contact_key = _normalize_text(candidate.contact_name)
        matched_contact, contact_issue = resolve_invoice_contact_match(
            _invoice_row_from_supplier_candidate(candidate),
            existing_contacts_by_preview_key,
            normalize_text=_normalize_text,
        )
        if contact_issue is not None:
            raise ValueError(format_row_issue(contact_issue))
        if matched_contact is None:
            contact = Contact(nom=candidate.contact_name, type=ContactType.FOURNISSEUR)
            db.add(contact)
            await db.flush()
            existing_contacts_by_preview_key.setdefault(contact_key, []).append(contact)
            result.contacts_created += 1
            result.record_created_object(
                sheet_name=sheet_name,
                kind="contacts",
                object_type="contact",
                object_id=contact.id,
                reference=contact.nom,
                details={"created_from": "supplier_import"},
            )
        else:
            contact = matched_contact
            if contact.type == ContactType.CLIENT:
                contact.type = ContactType.LES_DEUX
        invoice = Invoice(
            number=candidate.invoice_number,
            type=InvoiceType.FOURNISSEUR,
            contact_id=contact.id,
            date=candidate.invoice_date,
            due_date=apply_default_due_date(
                candidate.invoice_date,
                None,
                default_invoice_due_days,
            ),
            total_amount=candidate.amount,
            paid_amount=Decimal("0"),
            status=InvoiceStatus.SENT,
            label=InvoiceLabel(candidate.label),
            description=candidate.description,
            reference=candidate.invoice_number,
        )
        db.add(invoice)
        await db.flush()
        created_invoice = True
        result.invoices_created += 1
        result.record_created_object(
            sheet_name=sheet_name,
            kind="invoices",
            object_type="invoice",
            object_id=invoice.id,
            reference=invoice.number,
            details={"contact_id": invoice.contact_id, "imported_from": "supplier_import"},
        )
    payment = Payment(
        invoice_id=invoice.id,
        contact_id=invoice.contact_id,
        amount=candidate.amount,
        date=candidate.invoice_date,
        method=PaymentMethod(candidate.payment_method),
        reference=candidate.invoice_number,
        notes=candidate.description,
    )
    db.add(payment)
    await db.flush()
    result.payments_created += 1
    result.record_created_object(
        sheet_name=sheet_name,
        kind="payments",
        object_type="payment",
        object_id=payment.id,
        reference=candidate.invoice_number,
        details={
            "invoice_id": payment.invoice_id,
            "contact_id": payment.contact_id,
            "amount": str(payment.amount),
        },
    )
    return invoice.id, payment.id, invoice.contact_id, created_invoice


# ---------------------------------------------------------------------------
# Main import functions
# ---------------------------------------------------------------------------
