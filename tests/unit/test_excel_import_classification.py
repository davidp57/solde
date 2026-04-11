"""Unit tests for Excel import worksheet classification helpers."""

from __future__ import annotations

from backend.services.excel_import_classification import (
    classify_comptabilite_sheet,
    classify_gestion_sheet,
    sheet_has_content,
)


class _FakeWorksheet:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self._rows = rows

    def iter_rows(self, *, values_only: bool) -> list[tuple[object, ...]]:
        assert values_only
        return self._rows


def test_sheet_has_content_detects_non_empty_cell() -> None:
    assert sheet_has_content(_FakeWorksheet([(None, ""), (None, "x")])) is True


def test_sheet_has_content_detects_empty_sheet() -> None:
    assert sheet_has_content(_FakeWorksheet([(None, ""), (None, None)])) is False


def test_classify_gestion_sheet_handles_supported_and_auxiliary_names() -> None:
    assert classify_gestion_sheet("Factures 2025") == ("invoices", None)
    assert classify_gestion_sheet("TODO import") == (None, "auxiliary-sheet")


def test_classify_gestion_sheet_returns_unmapped_for_unknown_sheet() -> None:
    assert classify_gestion_sheet("Synthese libre") == (None, "unmapped-sheet")


def test_classify_comptabilite_sheet_handles_entry_and_report_names() -> None:
    assert classify_comptabilite_sheet("Journal") == ("entries", None)
    assert classify_comptabilite_sheet("Grand livre") == (None, "report-sheet")


def test_classify_comptabilite_sheet_handles_entry_helper_sheet() -> None:
    assert classify_comptabilite_sheet("Journal (saisie)") == (
        None,
        "entry-helper-sheet",
    )
