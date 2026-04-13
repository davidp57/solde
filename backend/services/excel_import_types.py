"""Shared normalized row types for historical Excel import."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True)
class ParsedSheet:
    """Normalized header-level view of a worksheet."""

    header_row: int
    col_map: dict[str, int]
    missing_columns: list[str]


@dataclass(slots=True)
class RowValidationIssue:
    """Blocking validation issue attached to a source row."""

    source_row_number: int
    message: str


@dataclass(slots=True)
class RowIgnoredIssue:
    """Ignored row with explicit reason."""

    source_row_number: int
    message: str


@dataclass(slots=True)
class NormalizedInvoiceRow:
    """Validated invoice row ready for preview or persistence."""

    source_row_number: int
    invoice_date: date
    amount: Decimal
    contact_name: str
    invoice_number: str | None
    label: str


@dataclass(slots=True)
class NormalizedPaymentRow:
    """Validated payment row ready for preview or persistence."""

    source_row_number: int
    payment_date: date
    amount: Decimal
    method: str
    invoice_ref: str
    contact_name: str
    cheque_number: str | None
    deposited: bool
    deposit_date: date | None


@dataclass(slots=True)
class NormalizedSalaryRow:
    """Validated salary row ready for preview or persistence."""

    source_row_number: int
    month: str
    employee_name: str
    hours: Decimal
    gross: Decimal
    employee_charges: Decimal
    employer_charges: Decimal
    tax: Decimal
    net_pay: Decimal


@dataclass(slots=True)
class NormalizedContactRow:
    """Validated contact row ready for preview or persistence."""

    source_row_number: int
    nom: str
    prenom: str | None
    email: str | None


@dataclass(slots=True)
class NormalizedCashRow:
    """Validated cash movement row ready for preview or persistence."""

    source_row_number: int
    entry_date: date
    amount: Decimal
    movement_type: str
    reference: str | None
    contact_name: str | None
    description: str


@dataclass(slots=True)
class NormalizedBankRow:
    """Validated bank transaction row ready for preview or persistence."""

    source_row_number: int
    entry_date: date
    amount: Decimal
    reference: str | None
    description: str
    balance_after: Decimal


@dataclass(slots=True)
class NormalizedEntryRow:
    """Validated accounting entry row ready for preview or persistence."""

    source_row_number: int
    entry_date: date
    account_number: str
    label: str
    debit: Decimal
    credit: Decimal
    change_marker: str | None = None
