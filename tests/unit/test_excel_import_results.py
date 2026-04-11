"""Unit tests for Excel import result containers."""

from __future__ import annotations

from backend.services.excel_import_results import ImportResult, PreviewResult


def test_import_result_absorbs_preview_details() -> None:
    preview = PreviewResult()
    preview.errors.append("Factures — Ligne 2 : montant manquant")
    preview.warnings.append("Factures — ligne de total ignoree")
    preview.sheets.append(
        {
            "name": "Factures",
            "kind": "invoices",
            "ignored_rows": 1,
            "blocked_rows": 1,
            "warnings": ["ligne de total ignoree"],
            "errors": ["Ligne 2 : montant manquant"],
        }
    )

    result = ImportResult()
    result.absorb_preview(preview)
    payload = result.to_dict()

    assert result.ignored_rows == 1
    assert result.blocked_rows == 1
    assert result.skipped == 1
    assert result.errors == ["Factures — Ligne 2 : montant manquant"]
    assert result.warnings == ["Factures — ligne de total ignoree"]
    assert result.sheets[0]["errors"] == ["Ligne 2 : montant manquant"]
    assert payload["error_details"] == [
        {
            "category": "invoice-validation-error",
            "severity": "error",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": 2,
            "message": "montant manquant",
            "display_message": "Factures — Ligne 2 : montant manquant",
        }
    ]
    assert payload["warning_details"] == [
        {
            "category": "invoice-total",
            "severity": "warning",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": None,
            "message": "ligne de total ignoree",
            "display_message": "Factures — ligne de total ignoree",
        }
    ]
    assert payload["sheets"][0]["error_details"][0]["row_number"] == 2
    assert payload["sheets"][0]["error_details"][0]["category"] == "invoice-validation-error"
    assert payload["sheets"][0]["warning_details"][0]["message"] == "ligne de total ignoree"


def test_import_result_reset_persisted_counts_preserves_sheet_diagnostics() -> None:
    result = ImportResult()
    result.contacts_created = 2
    result.invoices_created = 3
    result.add_imported_row("Factures", "invoices", 2)
    result.record_created_object(
        sheet_name="Factures",
        kind="invoices",
        object_type="invoice",
        object_id=12,
        reference="F-2026-001",
    )

    result.reset_persisted_counts()

    assert result.contacts_created == 0
    assert result.invoices_created == 0
    assert result.sheets[0]["imported_rows"] == 0
    assert result.to_log_dict()["created_objects"] == []


def test_preview_result_to_dict_exposes_structured_issue_details() -> None:
    preview = PreviewResult()
    preview.errors.append("Factures — Ligne 3 : client manquant")
    preview.warnings.append("Aide - Factures — Feuille auxiliaire ignoree par la preview")
    preview.sheets.append(
        {
            "name": "Factures",
            "kind": "invoices",
            "status": "recognized",
            "header_row": 1,
            "rows": 1,
            "detected_columns": ["date", "montant"],
            "missing_columns": [],
            "ignored_rows": 0,
            "blocked_rows": 1,
            "sample_rows": [],
            "warnings": [],
            "errors": ["Ligne 3 : client manquant"],
        }
    )

    payload = preview.to_dict()

    assert payload["error_details"] == [
        {
            "category": "invoice-missing-contact",
            "severity": "error",
            "sheet_name": "Factures",
            "kind": "invoices",
            "row_number": 3,
            "message": "client manquant",
            "display_message": "Factures — Ligne 3 : client manquant",
        }
    ]
    assert payload["warning_details"] == [
        {
            "category": "gestion-auxiliary-sheet",
            "severity": "warning",
            "sheet_name": "Aide - Factures",
            "kind": None,
            "row_number": None,
            "message": "Feuille auxiliaire ignoree par la preview",
            "display_message": "Aide - Factures — Feuille auxiliaire ignoree par la preview",
        }
    ]
    assert payload["sheets"][0]["error_details"][0]["sheet_name"] == "Factures"


def test_preview_result_to_dict_uses_kind_specific_missing_columns_category() -> None:
    preview = PreviewResult()
    preview.errors.append(
        "Paiements — Colonnes requises manquantes: référence facture ou contact"
    )
    preview.sheets.append(
        {
            "name": "Paiements",
            "kind": "payments",
            "status": "unsupported",
            "header_row": 1,
            "rows": 0,
            "detected_columns": ["date", "montant"],
            "missing_columns": ["référence facture ou contact"],
            "ignored_rows": 0,
            "blocked_rows": 1,
            "sample_rows": [],
            "warnings": [],
            "errors": ["Colonnes requises manquantes: référence facture ou contact"],
        }
    )

    payload = preview.to_dict()

    assert payload["error_details"] == [
        {
            "category": "payment-missing-columns",
            "severity": "error",
            "sheet_name": "Paiements",
            "kind": "payments",
            "row_number": None,
            "message": "Colonnes requises manquantes: référence facture ou contact",
            "display_message": (
                "Paiements — Colonnes requises manquantes: "
                "référence facture ou contact"
            ),
        }
    ]
    assert payload["sheets"][0]["error_details"][0]["category"] == "payment-missing-columns"


def test_import_result_add_open_file_error_uses_stable_message() -> None:
    result = ImportResult()

    result.add_open_file_error(ValueError("boom"))

    assert result.errors == ["Impossible d'ouvrir le fichier : boom"]


def test_import_result_add_import_error_uses_given_scope() -> None:
    result = ImportResult()

    result.add_import_error("gestion", RuntimeError("panic"))

    assert result.errors == ["Erreur import gestion : panic"]


def test_preview_result_to_dict_categorizes_global_errors() -> None:
    preview = PreviewResult()
    preview.errors = [
        "Fichier deja importe (gestion) le 2026-04-11 12:34:56",
        "Import comptabilite bloque : des ecritures auto-generees "
        "issues de la gestion existent deja en base (2).",
    ]

    payload = preview.to_dict()

    assert payload["error_details"] == [
        {
            "category": "already-imported",
            "severity": "error",
            "sheet_name": None,
            "kind": None,
            "row_number": None,
            "message": "Fichier deja importe (gestion) le 2026-04-11 12:34:56",
            "display_message": "Fichier deja importe (gestion) le 2026-04-11 12:34:56",
        },
        {
            "category": "comptabilite-coexistence-blocked",
            "severity": "error",
            "sheet_name": None,
            "kind": None,
            "row_number": None,
            "message": (
                "Import comptabilite bloque : des ecritures auto-generees "
                "issues de la gestion existent deja en base (2)."
            ),
            "display_message": (
                "Import comptabilite bloque : des ecritures auto-generees "
                "issues de la gestion existent deja en base (2)."
            ),
        },
    ]
