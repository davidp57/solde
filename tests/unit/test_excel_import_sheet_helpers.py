"""Unit tests for Excel import sheet structure helpers."""

from __future__ import annotations

from backend.services.excel_import_sheet_helpers import (
    compose_description,
    detect_header_row,
    find_col_idx,
    find_invoice_number_idx,
    get_row_value,
    row_contains_text,
    row_text_values,
)


class _FakeWorksheet:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self._rows = rows

    def iter_rows(
        self,
        *,
        max_row: int | None = None,
        min_row: int | None = None,
        values_only: bool,
    ) -> list[tuple[object, ...]]:
        assert values_only
        rows = self._rows
        if min_row is not None:
            rows = rows[min_row - 1 :]
        if max_row is not None:
            rows = rows[:max_row]
        return rows


def test_detect_header_row_returns_index_and_normalized_columns() -> None:
    worksheet = _FakeWorksheet(
        [
            ("Titre", None, None),
            ("Date facture", "Réf facture", "Montant total"),
            ("2026-01-01", "F-1", 10),
        ]
    )

    header_info = detect_header_row(worksheet, ["montant", "date"])

    assert header_info == (2, {"date facture": 0, "ref facture": 1, "montant total": 2})


def test_find_col_idx_matches_normalized_fragment() -> None:
    col_map = {"date facture": 0, "ref facture": 1, "montant total": 2}
    assert find_col_idx(col_map, "montant") == 2


def test_find_invoice_number_idx_skips_excluded_and_false_positives() -> None:
    col_map = {
        "date facture": 0,
        "etat facture": 1,
        "montant facture": 2,
        "ref facture": 3,
    }
    assert find_invoice_number_idx(col_map, exclude_idx=0) == 3


def test_get_row_value_returns_none_for_missing_index() -> None:
    assert get_row_value(("a", "b"), 4) is None
    assert get_row_value(("a", "b"), None) is None


def test_row_text_values_and_contains_text_are_normalized() -> None:
    row = ("  Remise espèces  ", None, "Crédit Mutuel")
    assert row_text_values(row) == ["remise especes", "credit mutuel"]
    assert row_contains_text(row, "especes") is True
    assert row_contains_text(row, "banque") is False


def test_compose_description_deduplicates_and_keeps_order() -> None:
    description = compose_description(" Crédit Mutuel ", "remise espèces", "credit mutuel")
    assert description == "Crédit Mutuel ; remise espèces"
