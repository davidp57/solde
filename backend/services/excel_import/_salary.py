"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Any

from backend.services.excel_import._constants import (
    _SALARY_ACCRUAL_ACCOUNT_PREFIXES,
    _SALARY_MONTH_RE,
    _SALARY_PAYMENT_ACCOUNT_PREFIXES,
    _SALARY_TRAILING_INITIAL_RE,
)
from backend.services.excel_import._invoices import _normalize_decimal_text
from backend.services.excel_import_parsing import (
    normalize_text as _normalize_text,
)
from backend.services.excel_import_parsing import (
    parse_str as _parse_str,
)
from backend.services.excel_import_types import (
    NormalizedEntryRow,
    NormalizedSalaryRow,
)


def _salary_month_label(month: str) -> str:
    return month.replace("-", ".")


def _salary_entry_date(month: str) -> date:
    year_value, month_value = month.split("-")
    return date(int(year_value), int(month_value), 1)


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
