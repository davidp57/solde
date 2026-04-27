"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from backend.config import get_settings
from backend.services.excel_import._constants import (
    _COMPTABILITE_FILE_YEAR_RE,
    _GESTION_FILE_YEAR_RE,
    _SALARY_MONTH_RE,
    _IssueT,
)
from backend.services.excel_import._invoices import _normalize_decimal_text
from backend.services.excel_import._salary import _salary_employee_key
from backend.services.excel_import_parsing import (
    normalize_text as _normalize_text,
)
from backend.services.excel_import_parsing import (
    parse_date as _parse_date,
)
from backend.services.excel_import_parsing import (
    parse_str as _parse_str,
)
from backend.services.excel_import_sheet_helpers import (
    get_row_value as _get_row_value,
)
from backend.services.excel_import_types import (
    ParsedSheet,
    RowValidationIssue,
)


def _gestion_payment_comparison_signature(
    *,
    reference: str,
    payment_date: date,
    amount: Decimal,
    settlement_account: str,
    cheque_number: str | None = None,
) -> tuple[str, str, str, str, str]:
    return (
        _normalize_text(reference),
        payment_date.isoformat(),
        _normalize_decimal_text(amount),
        _normalize_text(settlement_account),
        (
            _normalize_text(cheque_number or "")
            if _normalize_text(settlement_account) == "511200"
            else ""
        ),
    )


def _gestion_salary_comparison_signature(
    *,
    month: str,
    employee_name: str,
    gross: Decimal,
    net_pay: Decimal,
) -> tuple[str, str, str, str]:
    return (
        month,
        _salary_employee_key(employee_name),
        _normalize_decimal_text(gross),
        _normalize_decimal_text(net_pay),
    )


def _gestion_bank_comparison_signature(
    *,
    entry_date: date,
    amount: Decimal,
    description: str,
    reference: str | None,
) -> tuple[str, str, str, str]:
    return (
        entry_date.isoformat(),
        _normalize_decimal_text(amount),
        _normalize_text(description),
        _normalize_text(reference or ""),
    )


def _gestion_cash_comparison_signature(
    *,
    entry_date: date,
    movement_type: str,
    amount: Decimal,
    description: str,
    reference: str | None,
) -> tuple[str, str, str, str, str]:
    return (
        entry_date.isoformat(),
        _normalize_text(movement_type),
        _normalize_decimal_text(amount),
        _normalize_text(description),
        _normalize_text(reference or ""),
    )


def _build_extra_in_solde_summary(*parts: str | None) -> str:
    return " · ".join(part for part in parts if part)


def _make_gestion_invoice_extra_detail(number: str, invoice_date: date) -> dict[str, str]:
    number_value = number.strip()
    date_value = invoice_date.isoformat()
    return {
        "summary": _build_extra_in_solde_summary(number_value, date_value),
        "number": number_value,
        "date": date_value,
    }


def _make_gestion_payment_extra_detail(
    *,
    reference: str,
    payment_date: date,
    amount: Decimal,
    settlement_account: str,
    cheque_number: str | None,
    invoice_number: str | None,
    invoice_reference: str | None,
) -> dict[str, str]:
    reference_value = reference.strip()
    payment_date_value = payment_date.isoformat()
    amount_value = _normalize_decimal_text(amount)
    settlement_account_value = settlement_account.strip()
    detail = {
        "summary": _build_extra_in_solde_summary(
            reference_value,
            payment_date_value,
            amount_value,
            settlement_account_value,
        ),
        "reference": reference_value,
        "payment_date": payment_date_value,
        "amount": amount_value,
        "settlement_account": settlement_account_value,
    }
    if cheque_number:
        detail["cheque_number"] = cheque_number.strip()
    if invoice_number:
        detail["invoice_number"] = invoice_number.strip()
    if invoice_reference:
        detail["invoice_reference"] = invoice_reference.strip()
    return detail


def _make_gestion_salary_extra_detail(
    *,
    month: str,
    employee_name: str,
    gross: Decimal,
    net_pay: Decimal,
) -> dict[str, str]:
    month_value = month.strip()
    employee_name_value = employee_name.strip()
    gross_value = _normalize_decimal_text(gross)
    net_pay_value = _normalize_decimal_text(net_pay)
    return {
        "summary": _build_extra_in_solde_summary(
            month_value,
            employee_name_value,
            gross_value,
            net_pay_value,
        ),
        "month": month_value,
        "employee_name": employee_name_value,
        "gross": gross_value,
        "net_pay": net_pay_value,
    }


def _make_gestion_bank_extra_detail(
    *,
    entry_date: date,
    amount: Decimal,
    description: str,
    reference: str | None,
) -> dict[str, str]:
    entry_date_value = entry_date.isoformat()
    amount_value = _normalize_decimal_text(amount)
    description_value = description.strip()
    reference_value = reference.strip() if reference else ""
    detail = {
        "summary": _build_extra_in_solde_summary(
            entry_date_value,
            amount_value,
            description_value,
            reference_value,
        ),
        "entry_date": entry_date_value,
        "amount": amount_value,
        "description": description_value,
    }
    if reference_value:
        detail["reference"] = reference_value
    return detail


def _make_gestion_cash_extra_detail(
    *,
    entry_date: date,
    movement_type: str,
    amount: Decimal,
    description: str,
    reference: str | None,
) -> dict[str, str]:
    entry_date_value = entry_date.isoformat()
    movement_type_value = movement_type.strip()
    amount_value = _normalize_decimal_text(amount)
    description_value = description.strip()
    reference_value = reference.strip() if reference else ""
    detail = {
        "summary": _build_extra_in_solde_summary(
            entry_date_value,
            movement_type_value,
            amount_value,
            description_value,
            reference_value,
        ),
        "entry_date": entry_date_value,
        "movement_type": movement_type_value,
        "amount": amount_value,
        "description": description_value,
    }
    if reference_value:
        detail["reference"] = reference_value
    return detail


def _expand_date_bounds(
    start_date: date | None,
    end_date: date | None,
    candidate_date: date,
) -> tuple[date, date]:
    if start_date is None or candidate_date < start_date:
        start_date = candidate_date
    if end_date is None or candidate_date > end_date:
        end_date = candidate_date
    return start_date, end_date


def _is_within_date_bounds(
    candidate_date: date,
    start_date: date | None,
    end_date: date | None,
) -> bool:
    if start_date is not None and candidate_date < start_date:
        return False
    return end_date is None or candidate_date <= end_date


def _gestion_file_fiscal_year_bounds(file_name: str | None) -> tuple[date, date] | None:
    return _preview_file_fiscal_year_bounds(file_name)


def _preview_file_fiscal_year_bounds(file_name: str | None) -> tuple[date, date] | None:
    if not file_name:
        return None

    match = _GESTION_FILE_YEAR_RE.search(file_name)
    if match is None:
        match = _COMPTABILITE_FILE_YEAR_RE.search(file_name)
    if match is None:
        return None

    fiscal_year_start_month = get_settings().fiscal_year_start_month
    start_year = int(match.group(1))
    start_date = date(start_year, fiscal_year_start_month, 1)
    next_fiscal_year_start = date(start_year + 1, fiscal_year_start_month, 1)
    return start_date, next_fiscal_year_start - timedelta(days=1)


@dataclass(frozen=True, slots=True)
class _PreviewFilterWindow:
    start_date: date | None
    end_date: date | None


def _resolve_comparison_window(
    file_name: str | None,
    requested_start_date: date | None,
    requested_end_date: date | None,
) -> _PreviewFilterWindow | None:
    del file_name
    if requested_start_date is None and requested_end_date is None:
        return None
    return _PreviewFilterWindow(
        start_date=requested_start_date,
        end_date=requested_end_date,
    )


def _is_within_comparison_window(
    candidate_date: date,
    window: _PreviewFilterWindow | None,
) -> bool:
    if window is None:
        return True
    if window.start_date is not None and candidate_date < window.start_date:
        return False
    return window.end_date is None or candidate_date <= window.end_date


def _salary_month_to_date(month: str) -> date | None:
    match = _SALARY_MONTH_RE.match(month)
    if match is None:
        return None
    return date(int(match.group(1)), int(match.group(2)), 1)


def _is_salary_month_within_comparison_window(
    month: str,
    window: _PreviewFilterWindow | None,
) -> bool:
    if window is None:
        return True
    candidate_date = _salary_month_to_date(month)
    if candidate_date is None:
        return False
    return _is_within_comparison_window(candidate_date, window)


def _find_date_column_index(col_map: dict[str, int]) -> int | None:
    for column_name, column_index in col_map.items():
        if "date" in _normalize_text(column_name):
            return column_index
    return None


def _build_sheet_row_dates(
    ws: Any,
    parsed_sheet: ParsedSheet,
) -> dict[int, date]:
    date_column_index = _find_date_column_index(parsed_sheet.col_map)
    if date_column_index is None:
        return {}

    row_dates: dict[int, date] = {}
    for source_row_number, row in enumerate(ws.iter_rows(values_only=True), start=1):
        parsed_date = _parse_date(_get_row_value(row, date_column_index))
        if parsed_date is not None:
            row_dates[source_row_number] = parsed_date
    return row_dates


def _build_salary_row_months(ws: Any) -> dict[int, str]:
    row_months: dict[int, str] = {}
    current_month: str | None = None
    for source_row_number, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if all(cell is None for cell in row):
            continue
        first_cell = _parse_str(_get_row_value(row, 0))
        if not first_cell:
            continue
        if match := _SALARY_MONTH_RE.match(first_cell):
            current_month = f"{match.group(1)}-{match.group(2)}"
            continue
        if current_month is not None:
            row_months[source_row_number] = current_month
    return row_months


def _filter_date_issues_in_window(
    issues: list[_IssueT],
    row_dates: dict[int, date],
    window: _PreviewFilterWindow | None,
) -> list[_IssueT]:
    if window is None:
        return issues
    return [
        issue
        for issue in issues
        if (candidate_date := row_dates.get(issue.source_row_number)) is not None
        and _is_within_comparison_window(candidate_date, window)
    ]


def _filter_salary_issues_in_window(
    issues: list[RowValidationIssue],
    row_months: dict[int, str],
    window: _PreviewFilterWindow | None,
) -> list[RowValidationIssue]:
    if window is None:
        return issues
    return [
        issue
        for issue in issues
        if (month := row_months.get(issue.source_row_number)) is not None
        and _is_salary_month_within_comparison_window(month, window)
    ]


def _comparison_years_within_bounds(
    years: set[int],
    start_date: date | None,
    end_date: date | None,
) -> set[int]:
    if start_date is None or end_date is None:
        return years
    return set(range(start_date.year, end_date.year + 1))
