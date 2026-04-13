"""Unit tests for Excel import parsing helpers."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from backend.services.excel_import_parsing import (
    is_truthy_yes,
    normalize_invoice_label,
    normalize_payment_method,
    normalize_text,
    parse_date,
    parse_decimal,
    parse_str,
)


def test_parse_decimal_handles_french_format() -> None:
    assert parse_decimal("1 234,56") == Decimal("1234.56")


def test_parse_decimal_returns_none_for_invalid_value() -> None:
    assert parse_decimal("abc") is None


def test_parse_date_handles_datetime_and_string_formats() -> None:
    assert parse_date(datetime(2026, 4, 11, 10, 30, 0)) == date(2026, 4, 11)
    assert parse_date("11/04/2026") == date(2026, 4, 11)
    assert parse_date("2026-04-11") == date(2026, 4, 11)


def test_parse_str_truncates_when_requested() -> None:
    assert parse_str("  Bonjour  ", max_len=4) == "Bonj"


def test_normalize_text_is_accent_insensitive() -> None:
    assert normalize_text("Éncaissé") == "encaisse"


def test_normalize_payment_method_maps_common_labels() -> None:
    assert normalize_payment_method("Virement") == "virement"
    assert normalize_payment_method("Chèque") == "cheque"
    assert normalize_payment_method("Espèces") == "especes"


def test_normalize_invoice_label_maps_known_labels() -> None:
    assert normalize_invoice_label("cours scolaires") == "cs"
    assert normalize_invoice_label("adhésion annuelle") == "a"
    assert normalize_invoice_label("cours adhesion") == "cs+a"
    assert normalize_invoice_label("autre") == "general"


def test_is_truthy_yes_accepts_french_and_english_yes_values() -> None:
    assert is_truthy_yes("Oui") is True
    assert is_truthy_yes("ok") is True
    assert is_truthy_yes("non") is False
