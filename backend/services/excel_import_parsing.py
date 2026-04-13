"""Pure parsing and normalization helpers for historical Excel import."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

_SUPPLIER_INVOICE_REFERENCE_RE: re.Pattern[str] = re.compile(r"FF-\d{10}\.\d{2}\.\d{2}")


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


def normalize_text(value: Any) -> str:
    """Normalize text for accent-insensitive matching."""
    normalized = unicodedata.normalize("NFKD", parse_str(value).lower())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def format_contact_display_name(nom: Any, prenom: Any = None) -> str:
    """Format a contact name in the display order used by invoices and preview."""
    last_name = parse_str(nom)
    first_name = parse_str(prenom)
    return " ".join(part for part in (first_name, last_name) if part)


def _is_probable_uppercase_name_token(token: str) -> bool:
    letters = "".join(character for character in token if character.isalpha())
    return bool(letters) and letters == letters.upper()


def split_contact_full_name(nom: Any, prenom: Any = None) -> tuple[str, str | None]:
    """Split a legacy full name stored in nom into nom/prenom when the surname is uppercase."""
    last_name = parse_str(nom)
    first_name = parse_str(prenom) or None
    if first_name is not None or not last_name:
        return last_name, first_name

    tokens = last_name.split()
    if len(tokens) < 2:
        return last_name, None

    surname_start = len(tokens)
    while surname_start > 0 and _is_probable_uppercase_name_token(tokens[surname_start - 1]):
        surname_start -= 1

    if surname_start == 0 or surname_start == len(tokens):
        return last_name, None

    first_name_tokens = tokens[:surname_start]
    surname_tokens = tokens[surname_start:]
    if not any(not _is_probable_uppercase_name_token(token) for token in first_name_tokens):
        return last_name, None

    return " ".join(surname_tokens), " ".join(first_name_tokens)


def extract_supplier_invoice_reference(*values: Any) -> str | None:
    """Extract the first supplier invoice reference found, in argument priority order."""
    for value in values:
        text = parse_str(value)
        matches = _SUPPLIER_INVOICE_REFERENCE_RE.findall(text)
        if matches:
            return str(matches[-1])
    return None


def strip_supplier_invoice_reference(value: Any) -> str:
    """Remove supplier invoice references and trailing separators from free text."""
    text = parse_str(value, max_len=500)
    if not text:
        return ""
    cleaned = _SUPPLIER_INVOICE_REFERENCE_RE.sub("", text)
    cleaned = re.sub(r"(?:\s*[;-]\s*)+$", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def infer_supplier_contact_name(value: Any) -> str:
    """Infer the supplier contact name from a historical bank/cash description."""
    description = strip_supplier_invoice_reference(value)
    if not description:
        return ""
    if normalize_text(description).startswith("sous traitance des cours"):
        parts = [part.strip() for part in description.split(" - ") if part.strip()]
        if len(parts) >= 2:
            return parts[1]
    for separator in (" - ", " ; "):
        if separator in description:
            return description.split(separator, 1)[0].strip()
    return description


def is_supplier_subcontracting_description(value: Any) -> bool:
    """Return True when a supplier description corresponds to subcontracting courses."""
    return "sous traitance des cours" in normalize_text(strip_supplier_invoice_reference(value))


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
