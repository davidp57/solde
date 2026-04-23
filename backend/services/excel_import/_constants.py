"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TypeVar

from backend.services.excel_import_state import (
    load_existing_generated_accounting_group_signatures,
)
from backend.services.excel_import_types import (
    RowIgnoredIssue,
    RowValidationIssue,
)

logger = logging.getLogger(__name__)

_load_existing_generated_accounting_group_signatures = (
    load_existing_generated_accounting_group_signatures
)

_GESTION_IMPORT_ORDER = ("contacts", "invoices", "payments", "salaries", "cash", "bank")
_GESTION_FILE_YEAR_RE = re.compile(r"gestion\D*(20\d{2})", re.IGNORECASE)
_COMPTABILITE_FILE_YEAR_RE = re.compile(r"comptabilite\D*(20\d{2})", re.IGNORECASE)
_CLIENT_INVOICE_REFERENCE_RE = re.compile(r"\b\d{4}-\d{4}\b")
_SALARY_MONTH_RE = re.compile(r"\b(20\d{2})[.-](\d{2})\b")
_SALARY_TRAILING_INITIAL_RE = re.compile(r"\s+[a-z]$")
_SALARY_ACCRUAL_ACCOUNT_PREFIXES = ("421", "431", "443", "641", "645")
_SALARY_PAYMENT_ACCOUNT_PREFIXES = ("421", "512")
_CLIENT_INVOICE_CLARIFIED_MESSAGE = (
    "Facture client existante clarifiee a partir des ecritures comptables"
)


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


_IssueT = TypeVar("_IssueT", RowValidationIssue, RowIgnoredIssue)
