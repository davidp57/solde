"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import_classification import (
    classify_comptabilite_sheet as _classify_comptabilite_sheet,
)
from backend.services.excel_import_classification import (
    classify_gestion_sheet as _classify_gestion_sheet,
)
from backend.services.excel_import_classification import (
    sheet_has_content as _sheet_has_content,
)
from backend.services.excel_import_parsers import (
    parse_bank_sheet as _parse_bank_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_cash_sheet as _parse_cash_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_contact_sheet as _parse_contact_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_entries_sheet as _parse_entries_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_invoice_sheet as _parse_invoice_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_payment_sheet as _parse_payment_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_salary_sheet as _parse_salary_sheet_impl,
)
from backend.services.excel_import_parsing import (
    extract_supplier_invoice_reference as _extract_supplier_invoice_reference,
)
from backend.services.excel_import_parsing import (
    format_contact_display_name as _format_contact_display_name,
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
    parse_str as _parse_str,
)
from backend.services.excel_import_parsing import (
    split_contact_full_name as _split_contact_full_name,
)
from backend.services.excel_import_parsing import (
    strip_supplier_invoice_reference as _strip_supplier_invoice_reference,
)
from backend.services.excel_import_payment_matching import (
    PaymentMatchCandidate,
)
from backend.services.excel_import_payment_matching import (
    make_workbook_invoice_candidate as _make_workbook_invoice_candidate,
)
from backend.services.excel_import_payment_matching import (
    resolve_payment_match_with_database as _resolve_payment_match,
)
from backend.services.excel_import_policy import (
    COMPTABILITE_UNKNOWN_STRUCTURE_MESSAGE,
    ENTRY_EXISTING_MESSAGE,
    EXISTING_SALARY_MESSAGE,
    GESTION_UNKNOWN_STRUCTURE_MESSAGE,
    detect_gestion_preview_header,
    filter_duplicate_contact_rows,
    filter_duplicate_invoice_rows,
    find_ambiguous_invoice_contact_issues,
    find_existing_contact_issues,
    find_existing_invoice_issues,
    format_row_issue,
    make_existing_contact_issue,
    make_existing_invoice_issue,
    make_payment_resolution_issue,
    preview_warning_for_comptabilite_reason,
    preview_warning_for_gestion_reason,
    resolve_invoice_contact_match,
    should_ignore_cash_pending_deposit_forecast,
)
from backend.services.excel_import_preview_helpers import (
    append_finalized_sheet_preview as _append_finalized_sheet_preview,
)
from backend.services.excel_import_preview_helpers import (
    append_ignored_issues as _append_ignored_issues,
)
from backend.services.excel_import_preview_helpers import (
    append_preview_blocked_issue as _append_preview_blocked_issue,
)
from backend.services.excel_import_preview_helpers import (
    append_preview_ignored_issue as _append_preview_ignored_issue,
)
from backend.services.excel_import_preview_helpers import (
    append_preview_open_error as _append_preview_open_error,
)
from backend.services.excel_import_preview_helpers import (
    append_reasoned_ignored_sheet_preview as _append_reasoned_ignored_sheet_preview,
)
from backend.services.excel_import_preview_helpers import (
    append_row_issues as _append_row_issues,
)
from backend.services.excel_import_preview_helpers import (
    append_unknown_structure_sheet_preview as _append_unknown_structure_sheet_preview,
)
from backend.services.excel_import_preview_helpers import (
    contact_preview_key as _contact_preview_key,
)
from backend.services.excel_import_preview_helpers import (
    finalize_preview_can_import as _finalize_preview_can_import,
)
from backend.services.excel_import_preview_helpers import (
    find_sheet_preview as _find_sheet_preview,
)
from backend.services.excel_import_preview_helpers import (
    recompute_preview_can_import as _recompute_preview_can_import,
)
from backend.services.excel_import_preview_helpers import (
    register_preview_contact as _register_preview_contact,
)
from backend.services.excel_import_results import ImportResult, PreviewResult
from backend.services.excel_import_sheet_helpers import (
    detect_header_row as _detect_header_row,
)
from backend.services.excel_import_sheet_helpers import (
    get_row_value as _get_row_value,
)
from backend.services.excel_import_state import (
    accounting_entry_group_signature as _accounting_entry_group_signature,
)
from backend.services.excel_import_state import (
    accounting_entry_line_signature as _accounting_entry_line_signature,
)
from backend.services.excel_import_state import (
    accounting_entry_signature as _accounting_entry_signature,
)
from backend.services.excel_import_state import (
    add_comptabilite_coexistence_validation as _add_comptabilite_coexistence_validation,
)
from backend.services.excel_import_state import (
    compute_file_hash as _compute_file_hash,
)
from backend.services.excel_import_state import (
    find_successful_import_log as _find_successful_import_log,
)
from backend.services.excel_import_state import (
    load_existing_accounting_entry_signatures as _load_existing_accounting_entry_signatures,
)
from backend.services.excel_import_state import (
    load_existing_contacts_by_preview_key as _load_existing_contacts_by_preview_key,
)
from backend.services.excel_import_state import (
    load_existing_generated_accounting_group_signatures,
)
from backend.services.excel_import_state import (
    load_existing_invoice_numbers as _load_existing_invoice_numbers,
)
from backend.services.excel_import_state import (
    mark_preview_as_already_imported as _mark_preview_as_already_imported,
)
from backend.services.excel_import_state import (
    record_import_log as _record_import_log,
)
from backend.services.excel_import_types import (
    NormalizedBankRow,
    NormalizedCashRow,
    NormalizedContactRow,
    NormalizedEntryRow,
    NormalizedInvoiceRow,
    NormalizedPaymentRow,
    NormalizedSalaryRow,
    ParsedSheet,
    RowIgnoredIssue,
    RowValidationIssue,
)

logger = logging.getLogger(__name__)

_load_existing_generated_accounting_group_signatures = (
    load_existing_generated_accounting_group_signatures
)

_GESTION_IMPORT_ORDER = ("contacts", "invoices", "payments", "salaries", "cash", "bank")
_CLIENT_INVOICE_REFERENCE_RE = re.compile(r"\b\d{4}-\d{4}\b")
_SALARY_MONTH_RE = re.compile(r"\b(20\d{2})[.-](\d{2})\b")
_SALARY_TRAILING_INITIAL_RE = re.compile(r"\s+[a-z]$")
_SALARY_ACCRUAL_ACCOUNT_PREFIXES = ("421", "431", "443", "641", "645")
_SALARY_PAYMENT_ACCOUNT_PREFIXES = ("421", "512")


class _ImportSheetFailure(RuntimeError):
    """Internal marker used to abort the global import after a sheet-local failure."""


@dataclass(slots=True)
class _SupplierInvoiceCandidate:
    source_row_number: int
    invoice_date: date
    amount: Decimal
    invoice_number: str
    contact_name: str
    description: str
    label: str
    payment_method: str


def _salary_month_label(month: str) -> str:
    return month.replace("-", ".")


def _salary_entry_date(month: str) -> date:
    year_value, month_value = month.split("-")
    year_number = int(year_value)
    month_number = int(month_value)
    if month_number == 12:
        return date(year_number + 1, 1, 1)
    return date(year_number, month_number + 1, 1)


def _salary_employee_key(employee_name: str) -> str:
    key = _normalize_text(employee_name).replace(".", " ").strip()
    key = re.sub(r"\s+", " ", key)
    return _SALARY_TRAILING_INITIAL_RE.sub("", key)


def _extract_salary_month(*values: Any) -> str | None:
    matches: set[str] = set()
    for value in values:
        text = _parse_str(value, max_len=500)
        if not text:
            continue
        for year_part, month_part in _SALARY_MONTH_RE.findall(text):
            matches.add(f"{year_part}-{month_part}")
    if len(matches) != 1:
        return None
    return next(iter(matches))


def _accounting_amount_signature(
    *,
    account_number: str,
    debit: Decimal,
    credit: Decimal,
) -> str:
    return "|".join(
        (
            _normalize_text(account_number),
            _normalize_decimal_text(debit),
            _normalize_decimal_text(credit),
        )
    )


def _salary_group_amount_signature(
    lines: list[tuple[str, Decimal, Decimal]],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            _accounting_amount_signature(
                account_number=account_number,
                debit=debit,
                credit=credit,
            )
            for account_number, debit, credit in lines
            if debit > 0 or credit > 0
        )
    )


def _entry_group_amount_signature(
    entry_rows: list[NormalizedEntryRow],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            _accounting_amount_signature(
                account_number=entry_row.account_number,
                debit=entry_row.debit,
                credit=entry_row.credit,
            )
            for entry_row in entry_rows
            if entry_row.debit > 0 or entry_row.credit > 0
        )
    )


def _is_salary_related_label(label: str) -> bool:
    return (
        "salaire" in label
        or "charges salariales" in label
        or "charges patronales" in label
        or "impot sur le revenu" in label
    )


def _is_salary_accrual_like_entry_group(entry_rows: list[NormalizedEntryRow]) -> bool:
    account_numbers = [
        _normalize_text(entry_row.account_number)
        for entry_row in entry_rows
        if entry_row.debit > 0 or entry_row.credit > 0
    ]
    if not account_numbers:
        return False
    if any(account_number.startswith(("512", "53")) for account_number in account_numbers):
        return False
    return all(
        account_number.startswith(_SALARY_ACCRUAL_ACCOUNT_PREFIXES)
        for account_number in account_numbers
    )


def _is_salary_payment_like_entry_group(entry_rows: list[NormalizedEntryRow]) -> bool:
    account_numbers = [
        _normalize_text(entry_row.account_number)
        for entry_row in entry_rows
        if entry_row.debit > 0 or entry_row.credit > 0
    ]
    if not account_numbers:
        return False
    if not all(
        account_number.startswith(_SALARY_PAYMENT_ACCOUNT_PREFIXES)
        for account_number in account_numbers
    ):
        return False
    has_net_salary_debit = any(
        _normalize_text(entry_row.account_number).startswith("421") and entry_row.debit > 0
        for entry_row in entry_rows
    )
    has_salary_credit = any(
        _normalize_text(entry_row.account_number).startswith("512") and entry_row.credit > 0
        for entry_row in entry_rows
    )
    return has_net_salary_debit and has_salary_credit


def _salary_month_group_lines(
    month: str,
    salary_rows: list[NormalizedSalaryRow],
) -> list[list[tuple[str, str, Decimal, Decimal]]]:
    month_label = _salary_month_label(month)
    gross_total = sum((salary_row.gross for salary_row in salary_rows), Decimal("0"))
    employee_total = sum((salary_row.employee_charges for salary_row in salary_rows), Decimal("0"))
    employer_total = sum((salary_row.employer_charges for salary_row in salary_rows), Decimal("0"))
    tax_total = sum((salary_row.tax for salary_row in salary_rows), Decimal("0"))
    net_total = sum((salary_row.net_pay for salary_row in salary_rows), Decimal("0"))

    accrual_lines = [
        ("645100", f"Charges patronales {month_label}", employer_total, Decimal("0")),
        ("641000", f"Salaires bruts {month_label}", gross_total, Decimal("0")),
        ("421000", f"Salaires nets {month_label}", Decimal("0"), net_total),
        ("431100", f"Charges patronales {month_label}", Decimal("0"), employer_total),
        ("431100", f"Charges salariales {month_label}", Decimal("0"), employee_total),
    ]
    if tax_total > 0:
        accrual_lines.append(
            ("443000", f"Impôt sur le revenu {month_label}", Decimal("0"), tax_total)
        )

    payment_lines = [("421000", f"Paiement salaires {month_label}", net_total, Decimal("0"))]
    for salary_row in sorted(
        salary_rows, key=lambda row: (_salary_employee_key(row.employee_name), row.employee_name)
    ):
        if salary_row.net_pay <= 0:
            continue
        payment_lines.append(
            (
                "512100",
                f"Salaire {salary_row.employee_name} {month_label}",
                Decimal("0"),
                salary_row.net_pay,
            )
        )

    return [accrual_lines, payment_lines]


def _salary_month_group_signatures(
    month: str,
    salary_rows: list[NormalizedSalaryRow],
) -> set[tuple[str, ...]]:
    return {
        _salary_group_amount_signature(
            [(account_number, debit, credit) for account_number, _, debit, credit in group_lines]
        )
        for group_lines in _salary_month_group_lines(month, salary_rows)
    }


def _salary_month_standalone_tax_signatures(
    month: str,
    salary_rows: list[NormalizedSalaryRow],
) -> set[tuple[str, ...]]:
    tax_total = sum((salary_row.tax for salary_row in salary_rows), Decimal("0"))
    if tax_total <= 0:
        return set()

    signatures: set[tuple[str, ...]] = set()
    for account_number in ("431100", "443000"):
        signatures.add(
            (
                _accounting_amount_signature(
                    account_number=account_number,
                    debit=Decimal("0"),
                    credit=tax_total,
                ),
            )
        )
    return signatures


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


def _direct_bank_trigger_from_row(bank_row: NormalizedBankRow) -> tuple[Any, Decimal] | None:
    from backend.models.accounting_rule import TriggerType  # noqa: PLC0415

    description = _normalize_text(bank_row.description)
    reference = _normalize_text(bank_row.reference)
    combined_text = " ".join(part for part in (description, reference) if part)
    if "remise cheq" in combined_text and bank_row.amount > 0:
        return TriggerType.DEPOSIT_CHEQUES, bank_row.amount
    if "remise espe" in combined_text and bank_row.amount > 0:
        return TriggerType.DEPOSIT_ESPECES, bank_row.amount
    if "frais banc" in combined_text and bank_row.amount < 0:
        return TriggerType.BANK_FEES, abs(bank_row.amount)
    if "maif" in combined_text and bank_row.amount < 0:
        return TriggerType.BANK_INSURANCE, abs(bank_row.amount)
    if "interets" in combined_text and "livret bleu" in combined_text and bank_row.amount > 0:
        return TriggerType.BANK_SAVINGS_INTEREST, bank_row.amount
    if "virement interne" in combined_text:
        if bank_row.amount > 0:
            return TriggerType.BANK_INTERNAL_TRANSFER_FROM_SAVINGS, bank_row.amount
        if bank_row.amount < 0:
            return TriggerType.BANK_INTERNAL_TRANSFER_TO_SAVINGS, abs(bank_row.amount)
    if "urssaf" in combined_text and bank_row.amount < 0:
        return TriggerType.BANK_SOCIAL_CHARGES, abs(bank_row.amount)
    if "subvention" in combined_text and bank_row.amount > 0:
        return TriggerType.SUBSIDY_RECEIVED, bank_row.amount
    return None


async def _generate_direct_bank_entries(
    db: AsyncSession,
    *,
    bank_row: NormalizedBankRow,
    bank_entry: Any,
) -> list[Any]:
    from backend.models.accounting_entry import EntrySourceType  # noqa: PLC0415
    from backend.services.accounting_engine import generate_entries_for_trigger  # noqa: PLC0415

    direct_trigger = _direct_bank_trigger_from_row(bank_row)
    if direct_trigger is None:
        return []

    trigger, amount = direct_trigger
    return await generate_entries_for_trigger(
        db,
        trigger,
        amount,
        bank_row.entry_date,
        {
            "label": bank_row.description,
            "date": str(bank_row.entry_date),
        },
        source_type=EntrySourceType.GESTION,
        source_id=bank_entry.id,
    )


def _payment_signature(
    *,
    invoice_id: int,
    payment_date: date,
    amount: Decimal,
    method: str,
) -> tuple[int, str, str, str]:
    return (
        invoice_id,
        payment_date.isoformat(),
        format(amount.normalize(), "f"),
        _normalize_text(method),
    )


def _payment_row_from_bank_row(
    row: NormalizedBankRow,
    *,
    invoice_reference: str,
) -> NormalizedPaymentRow:
    return NormalizedPaymentRow(
        source_row_number=row.source_row_number,
        payment_date=row.entry_date,
        amount=row.amount,
        method="virement",
        invoice_ref=invoice_reference,
        contact_name="",
        cheque_number=None,
        deposited=True,
        deposit_date=row.entry_date,
    )


async def _load_existing_payment_signatures(
    db: AsyncSession,
) -> set[tuple[int, str, str, str]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.payment import Payment  # noqa: PLC0415

    result = await db.execute(
        select(Payment.invoice_id, Payment.date, Payment.amount, Payment.method)
    )
    return {
        _payment_signature(
            invoice_id=invoice_id,
            payment_date=payment_date,
            amount=amount,
            method=str(method),
        )
        for invoice_id, payment_date, amount, method in result.all()
    }


async def _load_existing_contacts_by_salary_key(db: AsyncSession) -> dict[str, Any]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415

    result = await db.execute(select(Contact))
    contacts_by_key: dict[str, Any] = {}
    for contact in result.scalars().all():
        display_name = _format_contact_display_name(contact.nom, contact.prenom) or contact.nom
        contacts_by_key.setdefault(_salary_employee_key(display_name), contact)
        contacts_by_key.setdefault(_salary_employee_key(contact.nom), contact)
    return contacts_by_key


async def _load_existing_salary_keys(db: AsyncSession) -> set[tuple[str, str]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415

    result = await db.execute(select(Salary.month, Contact.nom, Contact.prenom).join(Contact))
    return {
        (month, _salary_employee_key(_format_contact_display_name(nom, prenom) or nom))
        for month, nom, prenom in result.all()
    }


async def _load_existing_salary_group_signatures(
    db: AsyncSession,
) -> dict[str, set[tuple[str, ...]]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415

    result = await db.execute(
        select(
            Salary.month,
            Contact.nom,
            Contact.prenom,
            Salary.hours,
            Salary.gross,
            Salary.employee_charges,
            Salary.employer_charges,
            Salary.tax,
            Salary.net_pay,
        ).join(Contact)
    )

    salaries_by_month: dict[str, list[NormalizedSalaryRow]] = {}
    for (
        month,
        nom,
        prenom,
        hours,
        gross,
        employee_charges,
        employer_charges,
        tax,
        net_pay,
    ) in result.all():
        salaries_by_month.setdefault(month, []).append(
            NormalizedSalaryRow(
                source_row_number=0,
                month=month,
                employee_name=_format_contact_display_name(nom, prenom) or nom,
                hours=Decimal(str(hours)),
                gross=Decimal(str(gross)),
                employee_charges=Decimal(str(employee_charges)),
                employer_charges=Decimal(str(employer_charges)),
                tax=Decimal(str(tax)),
                net_pay=Decimal(str(net_pay)),
            )
        )

    return {
        month: _salary_month_group_signatures(month, salary_rows)
        | _salary_month_standalone_tax_signatures(month, salary_rows)
        for month, salary_rows in salaries_by_month.items()
    }


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
    existing_payment_signatures: set[tuple[int, str, str, str]],
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


async def import_gestion_file(
    db: AsyncSession, file_bytes: bytes, file_name: str | None = None
) -> ImportResult:
    """Import contacts, invoices and payments from a 'Gestion YYYY.xlsx' file.

    Expected sheets:
    - 'Factures' or 'Clients' : contact, date, montant, type, statut
    - 'Paiements' : date, contact, montant, mode, N° chèque

    The parser blocks recognized sheets containing invalid rows or unresolved payments.
    """
    import openpyxl  # noqa: PLC0415

    result = ImportResult()

    file_hash = _compute_file_hash(file_bytes)
    preview = await preview_gestion_file(db, file_bytes)
    if preview.errors:
        result.absorb_preview(preview)
        await _record_import_log(
            db,
            import_type="gestion",
            status="blocked",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    try:
        from io import BytesIO  # noqa: PLC0415

        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        result.add_open_file_error(exc)
        await _record_import_log(
            db,
            import_type="gestion",
            status="failed",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    sheets_by_kind: dict[str, list[Any]] = {kind: [] for kind in _GESTION_IMPORT_ORDER}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        kind, _ = _classify_gestion_sheet(sheet_name)
        if kind in sheets_by_kind:
            sheets_by_kind[kind].append(ws)

    for kind in _GESTION_IMPORT_ORDER:
        try:
            for ws in sheets_by_kind[kind]:
                if kind == "invoices":
                    await _import_invoices_sheet(db, ws, result)
                elif kind == "payments":
                    await _import_payments_sheet(db, ws, result)
                elif kind == "contacts":
                    await _import_contacts_sheet(db, ws, result)
                elif kind == "salaries":
                    await _import_salaries_sheet(db, ws, result)
                elif kind == "cash":
                    await _import_cash_sheet(db, ws, result)
                elif kind == "bank":
                    await _import_bank_sheet(db, ws, result)
        except Exception as exc:
            logger.error("Gestion import aborted during %s: %s", kind, exc, exc_info=True)
            await db.rollback()
            result.reset_persisted_counts()
            if not isinstance(exc, _ImportSheetFailure):
                result.add_import_error("gestion", exc)
            await _record_import_log(
                db,
                import_type="gestion",
                status="failed",
                file_hash=file_hash,
                file_name=file_name,
                result=result,
            )
            return result

    await _record_import_log(
        db,
        import_type="gestion",
        status="success",
        file_hash=file_hash,
        file_name=file_name,
        result=result,
    )
    return result


async def import_comptabilite_file(
    db: AsyncSession, file_bytes: bytes, file_name: str | None = None
) -> ImportResult:
    """Import accounting entries from a 'Comptabilité YYYY.xlsx' file.

    Expected sheet columns (flexible column detection):
    date | N° pièce | compte | libellé | débit | crédit
    """
    import openpyxl  # noqa: PLC0415

    result = ImportResult()

    file_hash = _compute_file_hash(file_bytes)
    preview = await preview_comptabilite_file(db, file_bytes)
    if preview.errors:
        result.absorb_preview(preview)
        await _record_import_log(
            db,
            import_type="comptabilite",
            status="blocked",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    try:
        from io import BytesIO  # noqa: PLC0415

        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        result.add_open_file_error(exc)
        await _record_import_log(
            db,
            import_type="comptabilite",
            status="failed",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    try:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            kind, _ = _classify_comptabilite_sheet(sheet_name)
            if kind == "entries":
                await _import_entries_sheet(db, ws, result)
    except Exception as exc:
        logger.error("Comptabilite import aborted: %s", exc, exc_info=True)
        await db.rollback()
        result.reset_persisted_counts()
        if not isinstance(exc, _ImportSheetFailure):
            result.add_import_error("comptabilite", exc)
        await _record_import_log(
            db,
            import_type="comptabilite",
            status="failed",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    await _record_import_log(
        db,
        import_type="comptabilite",
        status="success",
        file_hash=file_hash,
        file_name=file_name,
        result=result,
    )
    return result


def _is_cash_pending_deposit_forecast(
    row: tuple[Any, ...],
    *,
    tiers_idx: int | None,
    libelle_idx: int | None,
    raw_amount: Decimal | None,
) -> bool:
    """Recognize a cash-to-bank forecast row that should be ignored until dated."""
    return should_ignore_cash_pending_deposit_forecast(
        row,
        tiers_idx=tiers_idx,
        libelle_idx=libelle_idx,
        raw_amount=raw_amount,
        get_row_value=_get_row_value,
        parse_str=_parse_str,
        normalize_text=_normalize_text,
    )


def _parse_invoice_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedInvoiceRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    return _parse_invoice_sheet_impl(ws)


def _parse_payment_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedPaymentRow], list[RowValidationIssue]]:
    return _parse_payment_sheet_impl(ws)


def _parse_salary_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedSalaryRow], list[RowValidationIssue]]:
    return _parse_salary_sheet_impl(ws)


def _parse_contact_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedContactRow], list[RowValidationIssue]]:
    return _parse_contact_sheet_impl(ws)


def _parse_cash_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedCashRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    return _parse_cash_sheet_impl(ws)


def _parse_bank_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedBankRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    return _parse_bank_sheet_impl(ws)


def _parse_entries_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedEntryRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    return _parse_entries_sheet_impl(ws)


async def _import_contacts_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import contacts from a sheet."""
    from backend.models.contact import Contact, ContactType  # noqa: PLC0415

    parsed_sheet, normalized_rows, _ = _parse_contact_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    created_contacts: list[Contact] = []
    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    normalized_rows, ignored_issues = filter_duplicate_contact_rows(
        normalized_rows,
        normalize_text=_normalize_text,
    )
    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "contacts",
            format_row_issue(ignored_issue),
        )

    for contact_row in normalized_rows:
        preview_key = _contact_preview_key(contact_row.nom, contact_row.prenom)
        if existing_contacts_by_preview_key.get(preview_key):
            ignored_issue = make_existing_contact_issue(contact_row.source_row_number)
            result.add_ignored_row(
                ws.title,
                "contacts",
                format_row_issue(ignored_issue),
            )
            continue

        contact = Contact(
            nom=contact_row.nom,
            prenom=contact_row.prenom,
            email=contact_row.email,
            type=ContactType.CLIENT,
        )
        db.add(contact)
        created_contacts.append(contact)
        existing_contacts_by_preview_key.setdefault(preview_key, []).append(contact)
        result.contacts_created += 1
        result.add_imported_row(ws.title, "contacts")

    try:
        await db.flush()
        for contact in created_contacts:
            result.record_created_object(
                sheet_name=ws.title,
                kind="contacts",
                object_type="contact",
                object_id=contact.id,
                reference=_format_contact_display_name(contact.nom, contact.prenom),
            )
        logger.debug("Contacts import done — created=%d", result.contacts_created)
    except Exception as exc:
        logger.error("Contacts flush failed: %s", exc, exc_info=True)
        result.add_import_error("contacts", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_invoices_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import invoices from a sheet with flexible column detection."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact, ContactType  # noqa: PLC0415
    from backend.models.invoice import (  # noqa: PLC0415
        Invoice,
        InvoiceLabel,
        InvoiceStatus,
        InvoiceType,
    )

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_invoice_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    logger.debug(
        "Importing invoices sheet — rows=%s missing_columns=%s",
        len(normalized_rows),
        parsed_sheet.missing_columns,
    )

    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "invoices",
            format_row_issue(ignored_issue),
        )

    normalized_rows, ignored_issues = filter_duplicate_invoice_rows(
        normalized_rows,
        normalize_text=_normalize_text,
    )
    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "invoices",
            format_row_issue(ignored_issue),
        )

    created_invoices: list[Invoice] = []
    created_contacts: list[Contact] = []
    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    generated_number_index = 0
    for invoice_row in normalized_rows:
        invoice_date = invoice_row.invoice_date
        total = invoice_row.amount

        # Find or create contact
        contact_id: int | None = None
        contact_key = _normalize_text(invoice_row.contact_name)
        matched_contact, contact_issue = resolve_invoice_contact_match(
            invoice_row,
            existing_contacts_by_preview_key,
            normalize_text=_normalize_text,
        )
        if contact_issue is not None:
            raise ValueError(format_row_issue(contact_issue))
        if matched_contact is not None:
            contact_id = matched_contact.id
        else:
            contact_nom, contact_prenom = _split_contact_full_name(invoice_row.contact_name)
            new_contact = Contact(
                nom=contact_nom,
                prenom=contact_prenom,
                type=ContactType.CLIENT,
            )
            db.add(new_contact)
            await db.flush()
            created_contacts.append(new_contact)
            contact_id = new_contact.id
            existing_contacts_by_preview_key.setdefault(contact_key, []).append(new_contact)
            result.contacts_created += 1
            logger.debug(
                "Row %d — created contact '%s' (id=%s)",
                invoice_row.source_row_number,
                invoice_row.contact_name,
                contact_id,
            )
        if contact_id is None:
            result.skipped += 1
            continue

        number_raw = invoice_row.invoice_number or ""
        if not number_raw:
            generated_number_index += 1
            number_raw = f"IMP-{invoice_date.year}-{generated_number_index:04d}"

        # Idempotency: skip if already in DB
        existing_inv = await db.execute(select(Invoice).where(Invoice.number == number_raw))
        if existing_inv.scalar_one_or_none() is not None:
            ignored_issue = make_existing_invoice_issue(invoice_row.source_row_number)
            logger.debug(
                "Row %d — invoice '%s' already exists, skipping",
                invoice_row.source_row_number,
                number_raw,
            )
            result.add_ignored_row(
                ws.title,
                "invoices",
                format_row_issue(ignored_issue),
            )
            continue

        invoice = Invoice(
            number=number_raw,
            type=InvoiceType.CLIENT,
            contact_id=contact_id,
            date=invoice_date,
            total_amount=total,
            paid_amount=Decimal("0"),
            status=InvoiceStatus.SENT,
            label=InvoiceLabel(invoice_row.label),
        )
        db.add(invoice)
        created_invoices.append(invoice)
        logger.debug(
            "Row %d — invoice '%s' queued (contact_id=%d, amount=%s)",
            invoice_row.source_row_number,
            number_raw,
            contact_id,
            total,
        )
        result.invoices_created += 1
        result.add_imported_row(ws.title, "invoices")

    try:
        await db.flush()
        for contact in created_contacts:
            result.record_created_object(
                sheet_name=ws.title,
                kind="contacts",
                object_type="contact",
                object_id=contact.id,
                reference=_format_contact_display_name(contact.nom, contact.prenom),
                details={"created_from": "invoice_sheet"},
            )
        for inv_obj in created_invoices:
            result.record_created_object(
                sheet_name=ws.title,
                kind="invoices",
                object_type="invoice",
                object_id=inv_obj.id,
                reference=inv_obj.number,
                details={"contact_id": inv_obj.contact_id},
            )
        # Generate accounting entries for each new invoice (no-op if no rules configured)
        from backend.services.accounting_engine import (
            generate_entries_for_invoice,
        )  # noqa: PLC0415

        for inv_obj in created_invoices:
            try:
                entries = await generate_entries_for_invoice(db, inv_obj)
                result.entries_created += len(entries)
            except Exception as e:
                logger.debug("Accounting entries skipped for invoice '%s': %s", inv_obj.number, e)
                result.add_warning(
                    ws.title,
                    "invoices",
                    f"Ecritures comptables non generees pour la facture {inv_obj.number} : {e}",
                )
        logger.debug(
            "Invoices import done — created=%d skipped=%d entries=%d",
            result.invoices_created,
            result.skipped,
            result.entries_created,
        )
    except Exception as exc:
        logger.error("Invoices flush failed: %s", exc, exc_info=True)
        result.add_import_error("factures", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_payments_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import payments from a sheet."""
    from backend.models.invoice import InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    parsed_sheet, normalized_rows, _ = _parse_payment_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    logger.debug(
        "Importing payments sheet — rows=%s missing_columns=%s",
        len(normalized_rows),
        parsed_sheet.missing_columns,
    )

    created_payments: list[tuple[Payment, InvoiceType]] = []
    affected_invoice_ids: set[int] = set()
    for payment_row in normalized_rows:
        pay_date = payment_row.payment_date
        amount = payment_row.amount
        method = payment_row.method

        resolution = await _resolve_payment_match(db, payment_row)
        blocking_issue = make_payment_resolution_issue(
            source_row_number=payment_row.source_row_number,
            status=resolution.status,
            candidate=resolution.candidate,
            message=resolution.message,
            require_persistable_candidate=True,
        )
        if blocking_issue is not None:
            raise ValueError(format_row_issue(blocking_issue))

        candidate = resolution.candidate
        assert candidate is not None
        assert candidate.invoice_id is not None
        invoice_id = candidate.invoice_id
        contact_id = candidate.contact_id
        inv_type = candidate.invoice_type or InvoiceType.CLIENT

        payment = Payment(
            invoice_id=invoice_id,
            contact_id=contact_id,
            date=pay_date,
            amount=amount,
            method=method,
            cheque_number=payment_row.cheque_number,
            deposited=payment_row.deposited,
            deposit_date=payment_row.deposit_date,
        )
        db.add(payment)
        created_payments.append((payment, inv_type))
        affected_invoice_ids.add(invoice_id)
        logger.debug(
            "Row %d — payment %s queued (invoice_id=%d, amount=%s)",
            payment_row.source_row_number,
            pay_date,
            invoice_id,
            amount,
        )
        result.payments_created += 1
        result.add_imported_row(ws.title, "payments")

    try:
        await db.flush()
        for payment, _ in created_payments:
            result.record_created_object(
                sheet_name=ws.title,
                kind="payments",
                object_type="payment",
                object_id=payment.id,
                reference=str(payment.id) if payment.id is not None else None,
                details={
                    "invoice_id": payment.invoice_id,
                    "contact_id": payment.contact_id,
                    "amount": str(payment.amount),
                    "date": payment.date.isoformat(),
                },
            )
        # Refresh invoice statuses and generate accounting entries
        from backend.services.accounting_engine import (
            generate_entries_for_payment,
        )  # noqa: PLC0415
        from backend.services.payment import _refresh_invoice_status  # noqa: PLC0415

        for inv_id in affected_invoice_ids:
            await _refresh_invoice_status(db, inv_id)
        for p, p_inv_type in created_payments:
            try:
                entries = await generate_entries_for_payment(db, p, p_inv_type)
                result.entries_created += len(entries)
            except Exception as e:
                logger.debug("Accounting entries skipped for payment: %s", e)
                result.add_warning(
                    ws.title,
                    "payments",
                    f"Ecritures comptables non generees pour un paiement importe : {e}",
                )
        await db.flush()
        logger.debug(
            "Payments import done — created=%d skipped=%d entries=%d",
            result.payments_created,
            result.skipped,
            result.entries_created,
        )
    except Exception as exc:
        logger.error("Payments flush failed: %s", exc, exc_info=True)
        result.add_import_error("paiements", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_salaries_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import salary records from the historical `Aide Salaires` worksheet."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.accounting_entry import AccountingEntry, EntrySourceType  # noqa: PLC0415
    from backend.models.contact import Contact, ContactType  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415
    from backend.services.accounting_engine import _next_entry_number  # noqa: PLC0415
    from backend.services.fiscal_year_service import find_fiscal_year_id_for_date  # noqa: PLC0415

    parsed_sheet, normalized_rows, _ = _parse_salary_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    existing_contacts_by_salary_key = await _load_existing_contacts_by_salary_key(db)
    existing_salary_keys = await _load_existing_salary_keys(db)
    created_contacts: list[Contact] = []
    created_salaries: list[Salary] = []
    touched_months: set[str] = set()

    for salary_row in normalized_rows:
        employee_key = _salary_employee_key(salary_row.employee_name)
        contact = existing_contacts_by_salary_key.get(employee_key)
        if contact is None:
            contact = Contact(nom=salary_row.employee_name, type=ContactType.FOURNISSEUR)
            db.add(contact)
            await db.flush()
            created_contacts.append(contact)
            existing_contacts_by_salary_key[employee_key] = contact
            result.contacts_created += 1

        salary_key = (salary_row.month, employee_key)
        if salary_key in existing_salary_keys:
            result.add_ignored_row(
                ws.title,
                "salaries",
                format_row_issue(
                    RowIgnoredIssue(
                        source_row_number=salary_row.source_row_number,
                        message=EXISTING_SALARY_MESSAGE,
                    )
                ),
            )
            continue

        salary = Salary(
            employee_id=contact.id,
            month=salary_row.month,
            hours=salary_row.hours,
            gross=salary_row.gross,
            employee_charges=salary_row.employee_charges,
            employer_charges=salary_row.employer_charges,
            tax=salary_row.tax,
            net_pay=salary_row.net_pay,
            notes="Imported from Gestion Excel",
        )
        db.add(salary)
        created_salaries.append(salary)
        existing_salary_keys.add(salary_key)
        touched_months.add(salary_row.month)
        result.salaries_created += 1
        result.add_imported_row(ws.title, "salaries")

    try:
        await db.flush()
        for contact in created_contacts:
            result.record_created_object(
                sheet_name=ws.title,
                kind="salaries",
                object_type="contact",
                object_id=contact.id,
                reference=contact.nom,
                details={"created_from": "salary_sheet"},
            )
        for salary in created_salaries:
            result.record_created_object(
                sheet_name=ws.title,
                kind="salaries",
                object_type="salary",
                object_id=salary.id,
                reference=salary.month,
                details={"employee_id": salary.employee_id, "net_pay": str(salary.net_pay)},
            )

        existing_salary_entry_group_keys = {
            group_key
            for (group_key,) in (
                await db.execute(
                    select(AccountingEntry.group_key).where(
                        AccountingEntry.source_type == EntrySourceType.SALARY,
                        AccountingEntry.group_key.is_not(None),
                    )
                )
            ).all()
            if group_key
        }

        for month in sorted(touched_months):
            month_group_prefix = f"salary-import:{month}:"
            if any(
                group_key.startswith(month_group_prefix)
                for group_key in existing_salary_entry_group_keys
            ):
                continue

            month_result = await db.execute(
                select(
                    Salary.hours,
                    Salary.gross,
                    Salary.employee_charges,
                    Salary.employer_charges,
                    Salary.tax,
                    Salary.net_pay,
                    Contact.nom,
                    Contact.prenom,
                )
                .join(Contact, Contact.id == Salary.employee_id)
                .where(Salary.month == month)
                .order_by(Contact.nom, Contact.prenom, Salary.employee_id)
            )
            month_salary_rows = month_result.all()
            if not month_salary_rows:
                continue

            month_rows = [
                NormalizedSalaryRow(
                    source_row_number=0,
                    month=month,
                    employee_name=_format_contact_display_name(nom, prenom) or nom,
                    hours=Decimal(str(hours)),
                    gross=Decimal(str(gross)),
                    employee_charges=Decimal(str(employee_charges)),
                    employer_charges=Decimal(str(employer_charges)),
                    tax=Decimal(str(tax)),
                    net_pay=Decimal(str(net_pay)),
                )
                for (
                    hours,
                    gross,
                    employee_charges,
                    employer_charges,
                    tax,
                    net_pay,
                    nom,
                    prenom,
                ) in month_salary_rows
            ]
            entry_date = _salary_entry_date(month)
            fiscal_year_id = await find_fiscal_year_id_for_date(db, entry_date)

            for group_kind, group_lines in zip(
                ("accrual", "payment"),
                _salary_month_group_lines(month, month_rows),
                strict=True,
            ):
                group_key = f"salary-import:{month}:{group_kind}"
                for account_number, label, debit, credit in group_lines:
                    if debit <= 0 and credit <= 0:
                        continue
                    entry = AccountingEntry(
                        entry_number=await _next_entry_number(db),
                        date=entry_date,
                        account_number=account_number,
                        label=label,
                        debit=debit,
                        credit=credit,
                        fiscal_year_id=fiscal_year_id,
                        source_type=EntrySourceType.SALARY,
                        source_id=None,
                        group_key=group_key,
                    )
                    db.add(entry)
                    result.entries_created += 1

            existing_salary_entry_group_keys.add(f"salary-import:{month}:accrual")
            existing_salary_entry_group_keys.add(f"salary-import:{month}:payment")

        await db.flush()
        logger.debug("Salaries import done — created=%d", result.salaries_created)
    except Exception as exc:
        logger.error("Salaries flush failed: %s", exc, exc_info=True)
        result.add_import_error("salaires", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_cash_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import cash register movements from a 'Caisse' sheet.

    Expected columns (flexible): date | libellé/description | entrée | sortie
    or: date | description | montant | type (E/S or in/out)
    """
    from backend.models.cash import CashEntrySource, CashMovementType, CashRegister  # noqa: PLC0415
    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_invoice,
        generate_entries_for_payment,
    )
    from backend.services.cash_service import recompute_cash_balances  # noqa: PLC0415
    from backend.services.payment import _refresh_invoice_status  # noqa: PLC0415

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_cash_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        logger.debug(
            "Cash sheet skipped — header not detected or missing columns=%s",
            parsed_sheet.missing_columns if parsed_sheet else None,
        )
        return

    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "cash",
            format_row_issue(ignored_issue),
        )

    created_cash_entries: list[CashRegister] = []
    created_supplier_invoice_ids: set[int] = set()
    created_supplier_payment_ids: list[int] = []
    affected_invoice_ids: set[int] = set()
    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    for cash_row in normalized_rows:
        contact_id: int | None = None
        payment_id: int | None = None
        supplier_candidate = _supplier_invoice_candidate_from_cash_row(cash_row)
        if supplier_candidate is not None:
            (
                invoice_id,
                payment_id,
                contact_id,
                created_invoice,
            ) = await _ensure_supplier_invoice_payment(
                db,
                candidate=supplier_candidate,
                existing_contacts_by_preview_key=existing_contacts_by_preview_key,
                result=result,
                sheet_name=ws.title,
            )
            affected_invoice_ids.add(invoice_id)
            created_supplier_payment_ids.append(payment_id)
            if created_invoice:
                created_supplier_invoice_ids.add(invoice_id)
        entry = CashRegister(
            date=cash_row.entry_date,
            amount=cash_row.amount,
            type=CashMovementType(cash_row.movement_type),
            contact_id=contact_id,
            payment_id=payment_id,
            reference=cash_row.reference,
            description=cash_row.description,
            source=CashEntrySource.MANUAL,
            balance_after=Decimal("0"),
        )
        db.add(entry)
        created_cash_entries.append(entry)
        result.cash_created += 1
        result.add_imported_row(ws.title, "cash")

    try:
        await db.flush()
        if created_cash_entries:
            await recompute_cash_balances(db)
        for entry in created_cash_entries:
            result.record_created_object(
                sheet_name=ws.title,
                kind="cash",
                object_type="cash_register",
                object_id=entry.id,
                reference=entry.date.isoformat(),
                details={
                    "amount": str(entry.amount),
                    "type": str(entry.type),
                    "description": entry.description,
                },
            )
        for invoice_id in created_supplier_invoice_ids:
            invoice = await db.get(Invoice, invoice_id)
            if invoice is None:
                continue
            result.entries_created += len(await generate_entries_for_invoice(db, invoice))
        for invoice_id in affected_invoice_ids:
            await _refresh_invoice_status(db, invoice_id)
        for payment_id in created_supplier_payment_ids:
            supplier_payment = await db.get(Payment, payment_id)
            if supplier_payment is None:
                continue
            result.entries_created += len(
                await generate_entries_for_payment(db, supplier_payment, InvoiceType.FOURNISSEUR)
            )
        await db.flush()
        logger.debug("Cash import done — created=%d", result.cash_created)
    except Exception as exc:
        logger.error("Cash flush failed: %s", exc, exc_info=True)
        result.add_import_error("caisse", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_bank_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import bank transactions from a 'Banque' or 'Relevé' sheet.

    Expected columns (flexible): date | libellé | débit | crédit | solde
    or: date | description | montant (positive=credit, negative=debit)
    """
    from backend.models.bank import (
        BankTransaction,
        BankTransactionSource,
    )  # noqa: PLC0415
    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_invoice,
        generate_entries_for_payment,
    )
    from backend.services.payment import _refresh_invoice_status  # noqa: PLC0415

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_bank_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        logger.debug(
            "Bank sheet skipped — header not detected or missing columns=%s",
            parsed_sheet.missing_columns if parsed_sheet else None,
        )
        return

    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "bank",
            format_row_issue(ignored_issue),
        )

    created_bank_entries: list[tuple[BankTransaction, NormalizedBankRow]] = []
    created_payments: list[tuple[Payment, InvoiceType]] = []
    created_supplier_invoice_ids: set[int] = set()
    created_supplier_payment_ids: list[int] = []
    affected_invoice_ids: set[int] = set()
    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    existing_payment_signatures = await _load_existing_payment_signatures(db)
    for bank_row in normalized_rows:
        supplier_candidate = _supplier_invoice_candidate_from_bank_row(bank_row)
        if supplier_candidate is not None:
            invoice_id, payment_id, _, created_invoice = await _ensure_supplier_invoice_payment(
                db,
                candidate=supplier_candidate,
                existing_contacts_by_preview_key=existing_contacts_by_preview_key,
                result=result,
                sheet_name=ws.title,
            )
            affected_invoice_ids.add(invoice_id)
            created_supplier_payment_ids.append(payment_id)
            if created_invoice:
                created_supplier_invoice_ids.add(invoice_id)
        else:
            await _queue_client_payment_from_bank_row(
                db,
                bank_row=bank_row,
                existing_payment_signatures=existing_payment_signatures,
                created_payments=created_payments,
                affected_invoice_ids=affected_invoice_ids,
                result=result,
                sheet_name=ws.title,
            )
        entry = BankTransaction(
            date=bank_row.entry_date,
            amount=bank_row.amount,
            reference=bank_row.reference,
            description=bank_row.description,
            balance_after=bank_row.balance_after,
            source=BankTransactionSource.IMPORT,
        )
        db.add(entry)
        created_bank_entries.append((entry, bank_row))
        result.bank_created += 1
        result.add_imported_row(ws.title, "bank")

    try:
        await db.flush()
        for payment, _ in created_payments:
            result.record_created_object(
                sheet_name=ws.title,
                kind="payments",
                object_type="payment",
                object_id=payment.id,
                reference=payment.reference,
                details={
                    "invoice_id": payment.invoice_id,
                    "contact_id": payment.contact_id,
                    "amount": str(payment.amount),
                    "date": payment.date.isoformat(),
                },
            )
        for entry, _ in created_bank_entries:
            result.record_created_object(
                sheet_name=ws.title,
                kind="bank",
                object_type="bank_transaction",
                object_id=entry.id,
                reference=entry.date.isoformat(),
                details={
                    "amount": str(entry.amount),
                    "description": entry.description,
                    "balance_after": str(entry.balance_after),
                },
            )
        for entry, bank_row in created_bank_entries:
            result.entries_created += len(
                await _generate_direct_bank_entries(
                    db,
                    bank_row=bank_row,
                    bank_entry=entry,
                )
            )
        for invoice_id in created_supplier_invoice_ids:
            invoice = await db.get(Invoice, invoice_id)
            if invoice is None:
                continue
            result.entries_created += len(await generate_entries_for_invoice(db, invoice))
        for invoice_id in affected_invoice_ids:
            await _refresh_invoice_status(db, invoice_id)
        for payment_id in created_supplier_payment_ids:
            supplier_payment = await db.get(Payment, payment_id)
            if supplier_payment is None:
                continue
            result.entries_created += len(
                await generate_entries_for_payment(db, supplier_payment, InvoiceType.FOURNISSEUR)
            )
        for payment, invoice_type in created_payments:
            result.entries_created += len(
                await generate_entries_for_payment(db, payment, invoice_type)
            )
        await db.flush()
        logger.debug("Bank import done — created=%d", result.bank_created)
    except Exception as exc:
        logger.error("Bank flush failed: %s", exc, exc_info=True)
        result.add_import_error("banque", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_entries_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import accounting entries from a comptabilité sheet."""
    from sqlalchemy import func, select  # noqa: PLC0415

    from backend.models.accounting_entry import (
        AccountingEntry,
        EntrySourceType,
    )  # noqa: PLC0415
    from backend.services.fiscal_year_service import find_fiscal_year_id_for_date  # noqa: PLC0415

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_entries_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    existing_entry_signatures = await _load_existing_accounting_entry_signatures(db)
    existing_invoice_numbers = await _load_existing_invoice_numbers(db)
    existing_client_payment_signatures = await _load_existing_client_payment_reference_signatures(
        db
    )
    existing_supplier_payment_signatures = (
        await _load_existing_supplier_payment_reference_signatures(db)
    )
    existing_salary_group_signatures = await _load_existing_salary_group_signatures(db)
    existing_generated_group_signatures = (
        await _load_existing_generated_accounting_group_signatures(db)
    )
    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "entries",
            format_row_issue(ignored_issue),
        )

    # Pre-compute next entry number offset to avoid per-row DB queries
    count_result = await db.execute(select(func.count(AccountingEntry.id)))
    base_count = count_result.scalar_one_or_none() or 0
    entries_to_add: list[AccountingEntry] = []
    next_offset = 0
    for entry_group in _build_entry_row_groups(normalized_rows):
        if _matching_existing_client_invoice_reference(entry_group, existing_invoice_numbers):
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        )
                    ),
                )
            continue

        if _matching_existing_client_payment_reference(
            entry_group,
            existing_client_payment_signatures,
        ):
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        )
                    ),
                )
            continue

        if _matching_existing_supplier_invoice_payment_reference(
            entry_group,
            existing_supplier_payment_signatures,
        ):
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        )
                    ),
                )
            continue

        if _matching_existing_salary_entry_group(
            entry_group,
            existing_salary_group_signatures,
        ):
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        )
                    ),
                )
            continue

        if _normalized_entry_group_signature(entry_group) in existing_generated_group_signatures:
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        )
                    ),
                )
            continue

        group_key = f"import:{uuid4().hex}"
        for entry_row in entry_group:
            signature = _accounting_entry_signature(
                entry_date=entry_row.entry_date,
                account_number=entry_row.account_number,
                label=entry_row.label,
                debit=entry_row.debit,
                credit=entry_row.credit,
            )
            if signature in existing_entry_signatures:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        )
                    ),
                )
                continue

            next_offset += 1
            entry = AccountingEntry(
                entry_number=f"{base_count + next_offset:06d}",
                date=entry_row.entry_date,
                account_number=entry_row.account_number,
                label=entry_row.label,
                debit=entry_row.debit,
                credit=entry_row.credit,
                fiscal_year_id=await find_fiscal_year_id_for_date(db, entry_row.entry_date),
                source_type=EntrySourceType.MANUAL,
                group_key=group_key,
            )
            entries_to_add.append(entry)
            existing_entry_signatures.add(signature)
            result.add_imported_row(ws.title, "entries")

    try:
        for entry in entries_to_add:
            db.add(entry)
        await db.flush()
        for entry in entries_to_add:
            result.record_created_object(
                sheet_name=ws.title,
                kind="entries",
                object_type="accounting_entry",
                object_id=entry.id,
                reference=entry.entry_number,
                details={
                    "account_number": entry.account_number,
                    "date": entry.date.isoformat(),
                },
            )
        result.entries_created += len(entries_to_add)
        logger.debug("Entries import done — created=%d", result.entries_created)
    except Exception as exc:
        logger.error("Entries flush failed: %s", exc, exc_info=True)
        result.add_import_error("écritures", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _add_gestion_existing_rows_preview(
    db: AsyncSession, file_bytes: bytes, preview: PreviewResult
) -> None:
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    existing_contact_keys = set(existing_contacts_by_preview_key)
    existing_invoice_numbers = await _load_existing_invoice_numbers(db)
    existing_salary_keys = await _load_existing_salary_keys(db)

    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        kind, _ = _classify_gestion_sheet(sheet_name)
        sheet_preview = _find_sheet_preview(preview, sheet_name)
        if kind is None or sheet_preview is None or sheet_preview["status"] != "recognized":
            continue

        if kind == "contacts":
            parsed_sheet, contact_rows, _ = _parse_contact_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            contact_rows, _ = filter_duplicate_contact_rows(
                contact_rows,
                normalize_text=_normalize_text,
            )
            ignored_issues = find_existing_contact_issues(
                contact_rows,
                existing_contact_keys,
                contact_preview_key=_contact_preview_key,
            )
            for ignored_issue in ignored_issues:
                _append_preview_ignored_issue(
                    preview,
                    sheet_preview,
                    ignored_issue,
                )
            if ignored_count := len(ignored_issues):
                sheet_preview["rows"] = max(0, sheet_preview["rows"] - ignored_count)

        elif kind == "invoices":
            if (invoice_parsed := _parse_invoice_sheet(ws))[0] is None or invoice_parsed[
                0
            ].missing_columns:
                continue
            _, invoice_rows, _, _ = invoice_parsed
            invoice_rows, _ = filter_duplicate_invoice_rows(
                invoice_rows,
                normalize_text=_normalize_text,
            )
            ignored_issues = find_existing_invoice_issues(
                invoice_rows,
                existing_invoice_numbers,
                normalize_text=_normalize_text,
            )
            blocked_issues = find_ambiguous_invoice_contact_issues(
                invoice_rows,
                existing_contacts_by_preview_key,
                normalize_text=_normalize_text,
            )
            for ignored_issue in ignored_issues:
                _append_preview_ignored_issue(
                    preview,
                    sheet_preview,
                    ignored_issue,
                )
            for blocked_issue in blocked_issues:
                _append_preview_blocked_issue(
                    preview,
                    sheet_preview,
                    blocked_issue,
                )
            ignored_count = len(ignored_issues)
            blocked_count = len(blocked_issues)
            if ignored_count:
                sheet_preview["rows"] = max(0, sheet_preview["rows"] - ignored_count)
                preview.estimated_invoices = max(0, preview.estimated_invoices - ignored_count)
            if blocked_count:
                sheet_preview["rows"] = max(0, sheet_preview["rows"] - blocked_count)
                preview.estimated_invoices = max(0, preview.estimated_invoices - blocked_count)

        elif kind == "bank":
            parsed_sheet, bank_rows, _, _ = _parse_bank_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            for bank_row in bank_rows:
                candidate = _supplier_invoice_candidate_from_bank_row(bank_row)
                if candidate is None:
                    continue
                if _normalize_text(candidate.invoice_number) in existing_invoice_numbers:
                    _append_preview_ignored_issue(
                        preview,
                        sheet_preview,
                        make_existing_invoice_issue(candidate.source_row_number),
                    )
                    preview.estimated_invoices = max(0, preview.estimated_invoices - 1)
                    continue
                _, supplier_blocked_issue = resolve_invoice_contact_match(
                    _invoice_row_from_supplier_candidate(candidate),
                    existing_contacts_by_preview_key,
                    normalize_text=_normalize_text,
                )
                if supplier_blocked_issue is not None:
                    _append_preview_blocked_issue(
                        preview,
                        sheet_preview,
                        supplier_blocked_issue,
                    )
                    preview.estimated_invoices = max(0, preview.estimated_invoices - 1)
                    preview.estimated_payments = max(0, preview.estimated_payments - 1)

        elif kind == "cash":
            parsed_sheet, cash_rows, _, _ = _parse_cash_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            for cash_row in cash_rows:
                candidate = _supplier_invoice_candidate_from_cash_row(cash_row)
                if candidate is None:
                    continue
                if _normalize_text(candidate.invoice_number) in existing_invoice_numbers:
                    _append_preview_ignored_issue(
                        preview,
                        sheet_preview,
                        make_existing_invoice_issue(candidate.source_row_number),
                    )
                    preview.estimated_invoices = max(0, preview.estimated_invoices - 1)
                    continue
                _, supplier_blocked_issue = resolve_invoice_contact_match(
                    _invoice_row_from_supplier_candidate(candidate),
                    existing_contacts_by_preview_key,
                    normalize_text=_normalize_text,
                )
                if supplier_blocked_issue is not None:
                    _append_preview_blocked_issue(
                        preview,
                        sheet_preview,
                        supplier_blocked_issue,
                    )
                    preview.estimated_invoices = max(0, preview.estimated_invoices - 1)
                    preview.estimated_payments = max(0, preview.estimated_payments - 1)

        elif kind == "salaries":
            parsed_sheet, salary_rows, _ = _parse_salary_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            ignored_issues = [
                RowIgnoredIssue(
                    source_row_number=salary_row.source_row_number,
                    message=EXISTING_SALARY_MESSAGE,
                )
                for salary_row in salary_rows
                if (salary_row.month, _salary_employee_key(salary_row.employee_name))
                in existing_salary_keys
            ]
            for ignored_issue in ignored_issues:
                _append_preview_ignored_issue(
                    preview,
                    sheet_preview,
                    ignored_issue,
                )
            if ignored_count := len(ignored_issues):
                sheet_preview["rows"] = max(0, sheet_preview["rows"] - ignored_count)
                preview.estimated_salaries = max(0, preview.estimated_salaries - ignored_count)

    preview._candidate_contacts.difference_update(existing_contact_keys)
    preview.estimated_contacts = len(preview._candidate_contacts)
    _recompute_preview_can_import(preview)


async def _add_comptabilite_existing_rows_preview(
    db: AsyncSession, file_bytes: bytes, preview: PreviewResult
) -> None:
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    existing_entry_signatures = await _load_existing_accounting_entry_signatures(db)
    existing_invoice_numbers = await _load_existing_invoice_numbers(db)
    existing_client_payment_signatures = await _load_existing_client_payment_reference_signatures(
        db
    )
    existing_supplier_payment_signatures = (
        await _load_existing_supplier_payment_reference_signatures(db)
    )
    existing_salary_group_signatures = await _load_existing_salary_group_signatures(db)
    existing_generated_group_signatures = (
        await _load_existing_generated_accounting_group_signatures(db)
    )
    if (
        not existing_entry_signatures
        and not existing_generated_group_signatures
        and not existing_invoice_numbers
    ):
        return

    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        kind, _ = _classify_comptabilite_sheet(sheet_name)
        sheet_preview = _find_sheet_preview(preview, sheet_name)
        if kind != "entries" or sheet_preview is None or sheet_preview["status"] != "recognized":
            continue

        parsed_sheet, normalized_rows, _, _ = _parse_entries_sheet(ws)
        if parsed_sheet is None or parsed_sheet.missing_columns:
            continue

        for entry_group in _build_entry_row_groups(normalized_rows):
            if _matching_existing_client_invoice_reference(entry_group, existing_invoice_numbers):
                for entry_row in entry_group:
                    _append_preview_ignored_issue(
                        preview,
                        sheet_preview,
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        ),
                    )
                    preview.estimated_entries = max(0, preview.estimated_entries - 1)
                continue

            if _matching_existing_client_payment_reference(
                entry_group,
                existing_client_payment_signatures,
            ):
                for entry_row in entry_group:
                    _append_preview_ignored_issue(
                        preview,
                        sheet_preview,
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        ),
                    )
                    preview.estimated_entries = max(0, preview.estimated_entries - 1)
                continue

            if _matching_existing_supplier_invoice_payment_reference(
                entry_group,
                existing_supplier_payment_signatures,
            ):
                for entry_row in entry_group:
                    _append_preview_ignored_issue(
                        preview,
                        sheet_preview,
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        ),
                    )
                    preview.estimated_entries = max(0, preview.estimated_entries - 1)
                continue

            if _matching_existing_salary_entry_group(
                entry_group,
                existing_salary_group_signatures,
            ):
                for entry_row in entry_group:
                    _append_preview_ignored_issue(
                        preview,
                        sheet_preview,
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        ),
                    )
                    preview.estimated_entries = max(0, preview.estimated_entries - 1)
                continue

            if (
                _normalized_entry_group_signature(entry_group)
                in existing_generated_group_signatures
            ):
                for entry_row in entry_group:
                    _append_preview_ignored_issue(
                        preview,
                        sheet_preview,
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        ),
                    )
                    preview.estimated_entries = max(0, preview.estimated_entries - 1)
                continue

            for entry_row in entry_group:
                signature = _accounting_entry_signature(
                    entry_date=entry_row.entry_date,
                    account_number=entry_row.account_number,
                    label=entry_row.label,
                    debit=entry_row.debit,
                    credit=entry_row.credit,
                )
                if signature not in existing_entry_signatures:
                    continue
                _append_preview_ignored_issue(
                    preview,
                    sheet_preview,
                    RowIgnoredIssue(
                        source_row_number=entry_row.source_row_number,
                        message=ENTRY_EXISTING_MESSAGE,
                    ),
                )
                preview.estimated_entries = max(0, preview.estimated_entries - 1)

    _recompute_preview_can_import(preview)


async def _add_gestion_payment_validation(
    db: AsyncSession, file_bytes: bytes, preview: PreviewResult
) -> None:
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    workbook_candidates: list[PaymentMatchCandidate] = []
    payment_rows_by_sheet: dict[str, list[NormalizedPaymentRow]] = {}

    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        kind, _ = _classify_gestion_sheet(sheet_name)
        if kind == "invoices":
            parsed_sheet, invoice_rows, _, _ = _parse_invoice_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            workbook_candidates.extend(
                _make_workbook_invoice_candidate(invoice_row) for invoice_row in invoice_rows
            )
        elif kind == "payments":
            parsed_sheet, payment_rows, _ = _parse_payment_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            payment_rows_by_sheet[sheet_name] = payment_rows

    for sheet_name, payment_rows in payment_rows_by_sheet.items():
        sheet_preview = _find_sheet_preview(preview, sheet_name)
        if sheet_preview is None:
            continue

        payment_errors: list[str] = []
        for payment_row in payment_rows:
            resolution = await _resolve_payment_match(
                db,
                payment_row,
                workbook_candidates,
            )
            blocking_issue = make_payment_resolution_issue(
                source_row_number=payment_row.source_row_number,
                status=resolution.status,
                candidate=resolution.candidate,
                message=resolution.message,
                require_persistable_candidate=False,
            )
            if blocking_issue is not None:
                payment_errors.append(format_row_issue(blocking_issue))

        if payment_errors:
            sheet_preview["errors"].extend(payment_errors)
            preview.errors.extend(f"{sheet_name} — {error}" for error in payment_errors)


def _collect_sample_rows(
    ws: Any, header_row: int, col_map: dict[str, int], *, limit: int = 3
) -> list[dict[str, str]]:
    samples: list[dict[str, str]] = []
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if all(cell is None for cell in row):
            continue
        samples.append(
            {key: _parse_str(row[idx] if idx < len(row) else None) for key, idx in col_map.items()}
        )
        if len(samples) >= limit:
            break
    return samples


def _preview_sheet_gestion(ws: Any, sheet_name: str, preview: PreviewResult) -> None:
    """Count parseable rows and report diagnostics for gestion files."""
    kind, reason = _classify_gestion_sheet(sheet_name)
    if kind is None:
        _append_reasoned_ignored_sheet_preview(
            preview,
            sheet_name=sheet_name,
            has_content=_sheet_has_content(ws),
            warning=preview_warning_for_gestion_reason(reason),
        )
        return

    header_info = detect_gestion_preview_header(
        ws,
        kind,
        detect_header_row=_detect_header_row,
    )

    if header_info is None:
        _append_unknown_structure_sheet_preview(
            preview,
            sheet_name=sheet_name,
            kind=kind,
            warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
        )
        return

    header_row, col_map = header_info
    detected_columns = list(col_map.keys())
    count = 0
    missing_columns: list[str] = []
    ignored_rows = 0
    errors: list[str] = []
    warnings: list[str] = []

    if kind == "contacts":
        parsed_sheet, contact_rows, row_issues = _parse_contact_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        contact_rows, ignored_issues = filter_duplicate_contact_rows(
            contact_rows,
            normalize_text=_normalize_text,
        )
        ignored_rows = len(ignored_issues)
        count = len(contact_rows)
        _append_row_issues(errors, row_issues)
        _append_ignored_issues(warnings, ignored_issues)
        if not missing_columns:
            for contact_row in contact_rows:
                _register_preview_contact(
                    preview,
                    _format_contact_display_name(contact_row.nom, contact_row.prenom),
                )
    elif kind == "invoices":
        parsed_sheet, invoice_rows, row_issues, ignored_issues = _parse_invoice_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        invoice_rows, duplicate_ignored_issues = filter_duplicate_invoice_rows(
            invoice_rows,
            normalize_text=_normalize_text,
        )
        ignored_rows = len(ignored_issues) + len(duplicate_ignored_issues)
        count = len(invoice_rows)
        _append_row_issues(errors, row_issues)
        _append_ignored_issues(warnings, ignored_issues)
        _append_ignored_issues(warnings, duplicate_ignored_issues)
        if not missing_columns:
            for invoice_row in invoice_rows:
                _register_preview_contact(preview, invoice_row.contact_name)
            preview.estimated_invoices += count
    elif kind == "payments":
        parsed_sheet, payment_rows, row_issues = _parse_payment_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(payment_rows)
        _append_row_issues(errors, row_issues)
        if not missing_columns:
            for payment_row in payment_rows:
                if payment_row.contact_name:
                    _register_preview_contact(preview, payment_row.contact_name)
            preview.estimated_payments += count
    elif kind == "salaries":
        parsed_sheet, salary_rows, row_issues = _parse_salary_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(salary_rows)
        _append_row_issues(errors, row_issues)
        if not missing_columns:
            for salary_row in salary_rows:
                _register_preview_contact(preview, salary_row.employee_name)
            preview.estimated_salaries += count
    elif kind == "bank":
        parsed_sheet, bank_rows, row_issues, ignored_issues = _parse_bank_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(bank_rows)
        _append_row_issues(errors, row_issues)
        ignored_rows = len(ignored_issues)
        _append_ignored_issues(warnings, ignored_issues)
        if not missing_columns:
            for bank_row in bank_rows:
                candidate = _supplier_invoice_candidate_from_bank_row(bank_row)
                if candidate is not None:
                    preview.estimated_invoices += 1
                    preview.estimated_payments += 1
                    _register_preview_contact(preview, candidate.contact_name)
                    continue
                if _single_client_invoice_reference(bank_row.reference, bank_row.description):
                    preview.estimated_payments += 1
    elif kind == "cash":
        parsed_sheet, cash_rows, row_issues, ignored_issues = _parse_cash_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(cash_rows)
        _append_row_issues(errors, row_issues)
        ignored_rows = len(ignored_issues)
        _append_ignored_issues(warnings, ignored_issues)
        if not missing_columns:
            for cash_row in cash_rows:
                candidate = _supplier_invoice_candidate_from_cash_row(cash_row)
                if candidate is None:
                    continue
                preview.estimated_invoices += 1
                preview.estimated_payments += 1
                _register_preview_contact(preview, candidate.contact_name)

    assert parsed_sheet is not None
    col_map = parsed_sheet.col_map
    _append_finalized_sheet_preview(
        preview,
        sheet_name=sheet_name,
        kind=kind,
        header_row=header_row,
        rows=count,
        detected_columns=detected_columns,
        missing_columns=missing_columns,
        ignored_rows=ignored_rows,
        sample_rows=_collect_sample_rows(ws, header_row, col_map),
        warnings=warnings,
        errors=errors,
    )


def _preview_sheet_comptabilite(ws: Any, sheet_name: str, preview: PreviewResult) -> None:
    """Count parseable accounting entry rows and report diagnostics."""
    kind, reason = _classify_comptabilite_sheet(sheet_name)
    if kind is None:
        _append_reasoned_ignored_sheet_preview(
            preview,
            sheet_name=sheet_name,
            has_content=_sheet_has_content(ws),
            warning=preview_warning_for_comptabilite_reason(reason),
        )
        return

    parsed_sheet, normalized_rows, row_issues, ignored_issues = _parse_entries_sheet(ws)
    if parsed_sheet is None:
        _append_unknown_structure_sheet_preview(
            preview,
            sheet_name=sheet_name,
            kind=kind,
            warning=COMPTABILITE_UNKNOWN_STRUCTURE_MESSAGE,
        )
        return

    header_row = parsed_sheet.header_row
    detected_columns = list(parsed_sheet.col_map.keys())
    missing_columns = parsed_sheet.missing_columns
    count = len(normalized_rows)
    warnings: list[str] = []
    errors: list[str] = []
    _append_row_issues(errors, row_issues)
    _append_ignored_issues(warnings, ignored_issues)
    if not missing_columns:
        preview.estimated_entries += count

    _append_finalized_sheet_preview(
        preview,
        sheet_name=sheet_name,
        kind=kind,
        header_row=header_row,
        rows=count,
        detected_columns=detected_columns,
        missing_columns=missing_columns,
        ignored_rows=len(ignored_issues),
        sample_rows=_collect_sample_rows(ws, header_row, parsed_sheet.col_map),
        warnings=warnings,
        errors=errors,
    )


def _preview_gestion_file(file_bytes: bytes) -> PreviewResult:
    """Dry-run parse of a Gestion file using file-only validation."""
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    preview = PreviewResult()
    try:
        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        _append_preview_open_error(preview, exc)
        return preview

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        _preview_sheet_gestion(ws, sheet_name, preview)

    return preview


async def preview_gestion_file(db: AsyncSession, file_bytes: bytes) -> PreviewResult:
    """Dry-run parse of a Gestion file with shared business validation."""
    preview = _preview_gestion_file(file_bytes)
    if preview.errors:
        preview.can_import = False
        return preview

    await _add_gestion_existing_rows_preview(db, file_bytes, preview)

    import_log = await _find_successful_import_log(db, "gestion", _compute_file_hash(file_bytes))
    if import_log is not None:
        _mark_preview_as_already_imported(preview, "gestion", import_log)
        return preview

    await _add_gestion_payment_validation(db, file_bytes, preview)
    _finalize_preview_can_import(preview)
    return preview


async def preview_comptabilite_file(db: AsyncSession, file_bytes: bytes) -> PreviewResult:
    """Dry-run parse of a Comptabilité file — no DB writes."""
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    preview = PreviewResult()
    try:
        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        _append_preview_open_error(preview, exc)
        return preview

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        _preview_sheet_comptabilite(ws, sheet_name, preview)

    await _add_comptabilite_coexistence_validation(db, preview)
    await _add_comptabilite_existing_rows_preview(db, file_bytes, preview)
    if preview.errors:
        preview.can_import = False
        return preview

    import_log = await _find_successful_import_log(
        db, "comptabilite", _compute_file_hash(file_bytes)
    )
    if import_log is not None:
        _mark_preview_as_already_imported(preview, "comptabilite", import_log)
        return preview

    _finalize_preview_can_import(preview)

    return preview
