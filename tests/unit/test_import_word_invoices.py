"""Unit tests for scripts/import_word_invoices.py — date parsing helpers."""

from datetime import date

import sys
from pathlib import Path

# Make the scripts/ directory importable without installing as a package.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from import_word_invoices import _parse_date  # noqa: E402


class TestParseDateOrdinals:
    """_parse_date must handle French ordinal suffixes like '1er'."""

    def test_1er_month_year(self) -> None:
        assert _parse_date("Metz, le 1er avril 2025") == date(2025, 4, 1)

    def test_2eme_month_year(self) -> None:
        assert _parse_date("le 2ème janvier 2024") == date(2024, 1, 2)

    def test_3e_month_year(self) -> None:
        assert _parse_date("le 3e mars 2023") == date(2023, 3, 3)

    def test_no_ordinal(self) -> None:
        assert _parse_date("Metz, le 15 avril 2025") == date(2025, 4, 15)

    def test_slash_format(self) -> None:
        assert _parse_date("01/04/2025") == date(2025, 4, 1)

    def test_iso_format(self) -> None:
        assert _parse_date("2025-04-01") == date(2025, 4, 1)

    def test_embedded_in_sentence(self) -> None:
        assert _parse_date("Facture établie le 10er septembre 2022") == date(2022, 9, 10)

    def test_no_date_returns_none(self) -> None:
        assert _parse_date("Aucune date ici") is None

    def test_accented_month(self) -> None:
        assert _parse_date("le 5 février 2025") == date(2025, 2, 5)

    def test_aout_with_circumflex(self) -> None:
        assert _parse_date("le 12 août 2024") == date(2024, 8, 12)
