"""Pure parsing and normalization helpers for historical Excel import."""

from __future__ import annotations

import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def parse_decimal(value: Any) -> Decimal | None:
    """Parse a cell value into Decimal, returning None if not valid."""
    if value is None or value == "":
        return None
    try:
        cleaned = str(value).strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_date(value: Any) -> date | None:
    """Parse a cell value into date."""
    if value is None or value == "":
        return None
    if isinstance(value, (date, datetime)):
        return value.date() if isinstance(value, datetime) else value
    string_value = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(string_value, fmt).date()
        except ValueError:
            continue
    return None


def parse_str(value: Any, max_len: int | None = None) -> str:
    """Parse a cell value into str, optionally truncated."""
    if value is None:
        return ""
    string_value = str(value).strip()
    if max_len:
        string_value = string_value[:max_len]
    return string_value


def normalize_text(value: str) -> str:
    """Normalize text for accent-insensitive matching."""
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def normalize_payment_method(value: Any) -> str:
    """Map French payment method labels to system values."""
    string_value = parse_str(value).lower()
    if "vir" in string_value:
        return "virement"
    if "chq" in string_value or "chèq" in string_value or "che" in string_value:
        return "cheque"
    if "esp" in string_value or "cash" in string_value:
        return "especes"
    return "virement"


def normalize_invoice_label(value: Any) -> str:
    """Map workbook labels to invoice labels used by the domain model."""
    raw = normalize_text(parse_str(value))
    if raw in ("cs", "cours", "cours scolaires"):
        return "cs"
    if raw in ("a", "adhesion", "adhesion annuelle"):
        return "a"
    if raw in ("cs+a", "cours+adhesion", "cours adhesion"):
        return "cs+a"
    return "general"


def is_truthy_yes(value: Any) -> bool:
    """Return True for French/English truthy yes values."""
    return normalize_text(parse_str(value)) in {"oui", "yes", "true", "1", "ok"}
