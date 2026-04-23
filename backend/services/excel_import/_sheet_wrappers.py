"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

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
    normalize_text as _normalize_text,
)
from backend.services.excel_import_parsing import (
    parse_str as _parse_str,
)
from backend.services.excel_import_policy import (
    should_ignore_cash_pending_deposit_forecast,
)
from backend.services.excel_import_sheet_helpers import (
    get_row_value as _get_row_value,
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
