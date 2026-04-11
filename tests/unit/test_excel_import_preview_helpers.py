"""Unit tests for Excel import preview helpers."""

from __future__ import annotations

from dataclasses import dataclass

from backend.services.excel_import_preview_helpers import (
    append_finalized_sheet_preview,
    append_ignored_issues,
    append_ignored_sheet_preview,
    append_preview_blocked_issue,
    append_preview_ignored_issue,
    append_preview_open_error,
    append_reasoned_ignored_sheet_preview,
    append_row_issues,
    append_sheet_preview,
    append_unknown_structure_sheet_preview,
    contact_preview_key,
    finalize_preview_can_import,
    find_sheet_preview,
    make_sheet_preview,
    recompute_preview_can_import,
    register_preview_contact,
)
from backend.services.excel_import_results import PreviewResult


@dataclass(slots=True)
class _Issue:
    source_row_number: int
    message: str


def test_register_preview_contact_deduplicates_candidates() -> None:
    preview = PreviewResult()

    register_preview_contact(preview, "Christine LOPES")
    register_preview_contact(preview, "christine lopes")

    assert preview.estimated_contacts == 1
    assert contact_preview_key("Christine", "LOPES") == "christine lopes"


def test_make_and_append_sheet_preview_updates_global_lists() -> None:
    preview = PreviewResult()
    sheet = make_sheet_preview(
        sheet_name="Factures",
        kind="invoices",
        status="recognized",
        rows=2,
        sample_rows=[{"client": "Dupont"}],
        warnings=["ligne ignoree"],
        errors=["Ligne 2 : montant manquant"],
    )

    append_sheet_preview(preview, sheet)

    assert preview.can_import is True
    assert preview.sample_rows == [{"sheet": "Factures", "client": "Dupont"}]
    assert preview.warnings == ["Factures — ligne ignoree"]
    assert preview.errors == ["Factures — Ligne 2 : montant manquant"]


def test_append_issue_helpers_format_messages() -> None:
    warnings: list[str] = []
    errors: list[str] = []

    append_row_issues(errors, [_Issue(4, "montant manquant")])
    append_ignored_issues(warnings, [_Issue(7, "ligne de total ignoree")])

    assert errors == ["Ligne 4 : montant manquant"]
    assert warnings == ["Ligne 7 : ligne de total ignoree"]


def test_find_sheet_preview_and_append_preview_ignored_issue() -> None:
    preview = PreviewResult()
    sheet = make_sheet_preview(sheet_name="Factures", kind="invoices", status="recognized")
    preview.sheets.append(sheet)

    found = find_sheet_preview(preview, "Factures")
    assert found is sheet

    append_preview_ignored_issue(preview, sheet, _Issue(9, "ligne ignoree"))

    assert sheet["ignored_rows"] == 1
    assert sheet["warnings"] == ["Ligne 9 : ligne ignoree"]
    assert preview.warnings == ["Factures — Ligne 9 : ligne ignoree"]


def test_append_preview_blocked_issue_updates_sheet_and_global_errors() -> None:
    preview = PreviewResult()
    sheet = make_sheet_preview(sheet_name="Factures", kind="invoices", status="recognized")
    preview.sheets.append(sheet)

    append_preview_blocked_issue(preview, sheet, _Issue(11, "client ambigu"))

    assert sheet["blocked_rows"] == 1
    assert sheet["errors"] == ["Ligne 11 : client ambigu"]
    assert preview.errors == ["Factures — Ligne 11 : client ambigu"]


def test_append_ignored_sheet_preview_uses_given_status_and_warnings() -> None:
    preview = PreviewResult()

    append_ignored_sheet_preview(
        preview,
        sheet_name="TODO",
        kind="ignored",
        status="ignored",
        warnings=["Feuille auxiliaire ignoree par la preview"],
    )

    assert preview.sheets == [
        {
            "name": "TODO",
            "kind": "ignored",
            "status": "ignored",
            "header_row": None,
            "rows": 0,
            "detected_columns": [],
            "missing_columns": [],
            "ignored_rows": 0,
            "blocked_rows": 0,
            "sample_rows": [],
            "warnings": ["Feuille auxiliaire ignoree par la preview"],
            "errors": [],
        }
    ]
    assert preview.warnings == ["TODO — Feuille auxiliaire ignoree par la preview"]


def test_append_unknown_structure_sheet_preview_marks_sheet_ignored() -> None:
    preview = PreviewResult()

    append_unknown_structure_sheet_preview(
        preview,
        sheet_name="Paiements",
        kind="payments",
        warning="Structure non reconnue, feuille ignoree par la preview",
    )

    assert preview.sheets[0]["status"] == "ignored"
    assert preview.sheets[0]["warnings"] == [
        "Structure non reconnue, feuille ignoree par la preview"
    ]
    assert preview.warnings == [
        "Paiements — Structure non reconnue, feuille ignoree par la preview"
    ]


def test_append_reasoned_ignored_sheet_preview_marks_ignored_with_warning() -> None:
    preview = PreviewResult()

    append_reasoned_ignored_sheet_preview(
        preview,
        sheet_name="Aide - Factures",
        has_content=True,
        warning="Feuille auxiliaire ignoree par la preview",
    )

    assert preview.sheets[0]["status"] == "ignored"
    assert preview.sheets[0]["warnings"] == ["Feuille auxiliaire ignoree par la preview"]
    assert preview.warnings == [
        "Aide - Factures — Feuille auxiliaire ignoree par la preview"
    ]


def test_append_reasoned_ignored_sheet_preview_marks_empty_without_warning() -> None:
    preview = PreviewResult()

    append_reasoned_ignored_sheet_preview(
        preview,
        sheet_name="Vide",
        has_content=False,
        warning="Ne doit pas etre utilise",
    )

    assert preview.sheets[0]["status"] == "empty"
    assert preview.sheets[0]["warnings"] == []
    assert preview.warnings == []


def test_append_finalized_sheet_preview_marks_recognized_sheet_ready() -> None:
    preview = PreviewResult()

    append_finalized_sheet_preview(
        preview,
        sheet_name="Factures",
        kind="invoices",
        header_row=1,
        rows=2,
        detected_columns=["date", "montant"],
        missing_columns=[],
        ignored_rows=1,
        sample_rows=[{"client": "Dupont"}],
        warnings=["Ligne 4 : ligne ignoree"],
        errors=["Ligne 5 : client manquant"],
    )

    assert preview.sheets[0]["status"] == "recognized"
    assert preview.sheets[0]["blocked_rows"] == 1
    assert preview.sheets[0]["sample_rows"] == [{"client": "Dupont"}]
    assert preview.sample_rows == [{"sheet": "Factures", "client": "Dupont"}]


def test_append_finalized_sheet_preview_marks_unsupported_sheet_with_missing_columns() -> None:
    preview = PreviewResult()

    append_finalized_sheet_preview(
        preview,
        sheet_name="Paiements",
        kind="payments",
        header_row=1,
        rows=0,
        detected_columns=["date", "montant"],
        missing_columns=["référence facture ou contact"],
        ignored_rows=0,
        sample_rows=[],
        warnings=[],
        errors=[],
    )

    assert preview.sheets[0]["status"] == "unsupported"
    assert preview.sheets[0]["errors"] == [
        "Colonnes requises manquantes: référence facture ou contact"
    ]
    assert preview.errors == [
        "Paiements — Colonnes requises manquantes: référence facture ou contact"
    ]


def test_recompute_preview_can_import_reflects_recognized_rows() -> None:
    preview = PreviewResult()
    preview.sheets = [
        make_sheet_preview(sheet_name="Aide", kind="ignored", status="ignored", rows=3),
        make_sheet_preview(sheet_name="Factures", kind="invoices", status="recognized", rows=0),
    ]

    recompute_preview_can_import(preview)
    assert preview.can_import is False

    preview.sheets.append(
        make_sheet_preview(sheet_name="Paiements", kind="payments", status="recognized", rows=1)
    )
    recompute_preview_can_import(preview)
    assert preview.can_import is True


def test_finalize_preview_can_import_blocks_when_errors_exist() -> None:
    preview = PreviewResult()
    preview.can_import = True
    preview.errors = ["Factures — Ligne 4 : montant manquant"]

    finalize_preview_can_import(preview)

    assert preview.can_import is False


def test_finalize_preview_can_import_preserves_ready_preview_without_errors() -> None:
    preview = PreviewResult()
    preview.can_import = True

    finalize_preview_can_import(preview)

    assert preview.can_import is True


def test_append_preview_open_error_adds_stable_message() -> None:
    preview = PreviewResult()

    append_preview_open_error(preview, ValueError("boom"))

    assert preview.errors == ["Impossible d'ouvrir le fichier : boom"]
