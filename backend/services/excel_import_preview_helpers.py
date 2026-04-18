"""Preview and diagnostics helpers for historical Excel import."""

from __future__ import annotations

from typing import Any

from backend.services.excel_import_parsing import (
    format_contact_display_name,
    normalize_text,
    parse_str,
)
from backend.services.excel_import_policy import (
    format_missing_columns_issue,
    format_row_issue,
)
from backend.services.excel_import_results import PreviewResult


def register_preview_contact(preview: PreviewResult, value: Any) -> None:
    """Register a candidate contact name discovered during preview."""
    name = normalize_text(parse_str(value))
    if name:
        preview._candidate_contacts.add(name)
        preview.estimated_contacts = len(preview._candidate_contacts)


def contact_preview_key(nom: str, prenom: str | None = None) -> str:
    """Build the normalized preview key used for candidate contact counts."""
    return normalize_text(format_contact_display_name(nom, prenom))


def make_sheet_preview(
    *,
    sheet_name: str,
    kind: str,
    status: str,
    header_row: int | None = None,
    rows: int = 0,
    source_rows: int | None = None,
    detected_columns: list[str] | None = None,
    missing_columns: list[str] | None = None,
    ignored_rows: int = 0,
    policy_ignored_rows: int | None = None,
    blocked_rows: int = 0,
    initial_blocked_rows: int | None = None,
    sample_rows: list[dict[str, str]] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": sheet_name,
        "kind": kind,
        "status": status,
        "header_row": header_row,
        "rows": rows,
        "source_rows": rows if source_rows is None else source_rows,
        "detected_columns": detected_columns or [],
        "missing_columns": missing_columns or [],
        "ignored_rows": ignored_rows,
        "policy_ignored_rows": ignored_rows if policy_ignored_rows is None else policy_ignored_rows,
        "blocked_rows": blocked_rows,
        "initial_blocked_rows": (
            blocked_rows if initial_blocked_rows is None else initial_blocked_rows
        ),
        "sample_rows": sample_rows or [],
        "warnings": warnings or [],
        "errors": errors or [],
    }


def append_sheet_preview(preview: PreviewResult, sheet: dict[str, Any]) -> None:
    preview.sheets.append(sheet)
    preview.errors.extend(f"{sheet['name']} — {error}" for error in sheet["errors"])
    preview.warnings.extend(f"{sheet['name']} — {warning}" for warning in sheet["warnings"])
    if sheet["status"] == "recognized" and sheet["rows"] > 0:
        preview.can_import = True
        for row in sheet["sample_rows"]:
            if len(preview.sample_rows) >= 5:
                break
            preview.sample_rows.append({"sheet": sheet["name"], **row})


def append_ignored_sheet_preview(
    preview: PreviewResult,
    *,
    sheet_name: str,
    kind: str,
    status: str,
    warnings: list[str] | None = None,
) -> None:
    append_sheet_preview(
        preview,
        make_sheet_preview(
            sheet_name=sheet_name,
            kind=kind,
            status=status,
            warnings=warnings,
        ),
    )


def append_unknown_structure_sheet_preview(
    preview: PreviewResult,
    *,
    sheet_name: str,
    kind: str,
    warning: str,
) -> None:
    append_ignored_sheet_preview(
        preview,
        sheet_name=sheet_name,
        kind=kind,
        status="ignored",
        warnings=[warning],
    )


def append_reasoned_ignored_sheet_preview(
    preview: PreviewResult,
    *,
    sheet_name: str,
    has_content: bool,
    warning: str | None = None,
) -> None:
    status = "ignored" if has_content else "empty"
    warnings = [warning] if status == "ignored" and warning is not None else []
    append_ignored_sheet_preview(
        preview,
        sheet_name=sheet_name,
        kind="ignored",
        status=status,
        warnings=warnings,
    )


def append_finalized_sheet_preview(
    preview: PreviewResult,
    *,
    sheet_name: str,
    kind: str,
    header_row: int,
    rows: int,
    detected_columns: list[str],
    missing_columns: list[str],
    ignored_rows: int,
    sample_rows: list[dict[str, str]],
    warnings: list[str],
    errors: list[str],
) -> None:
    finalized_errors = list(errors)
    status = "recognized"
    if missing_columns:
        status = "unsupported"
        finalized_errors.append(format_missing_columns_issue(missing_columns))

    append_sheet_preview(
        preview,
        make_sheet_preview(
            sheet_name=sheet_name,
            kind=kind,
            status=status,
            header_row=header_row,
            rows=rows,
            source_rows=rows,
            detected_columns=detected_columns,
            missing_columns=missing_columns,
            ignored_rows=ignored_rows,
            policy_ignored_rows=ignored_rows,
            blocked_rows=len(finalized_errors),
            initial_blocked_rows=len(finalized_errors),
            sample_rows=sample_rows,
            warnings=warnings,
            errors=finalized_errors,
        ),
    )


def append_row_issues(errors: list[str], issues: list[Any]) -> None:
    errors.extend(format_row_issue(issue) for issue in issues)


def append_ignored_issues(warnings: list[str], issues: list[Any]) -> None:
    warnings.extend(format_row_issue(issue) for issue in issues)


def find_sheet_preview(preview: PreviewResult, sheet_name: str) -> dict[str, Any] | None:
    return next((sheet for sheet in preview.sheets if sheet["name"] == sheet_name), None)


def append_preview_ignored_issue(
    preview: PreviewResult,
    sheet_preview: dict[str, Any],
    issue: Any,
) -> None:
    message = format_row_issue(issue)
    sheet_preview["ignored_rows"] += 1
    sheet_preview["warnings"].append(message)
    preview.warnings.append(f"{sheet_preview['name']} — {message}")


def append_preview_blocked_issue(
    preview: PreviewResult,
    sheet_preview: dict[str, Any],
    issue: Any,
) -> None:
    message = format_row_issue(issue)
    sheet_preview["blocked_rows"] += 1
    sheet_preview["errors"].append(message)
    preview.errors.append(f"{sheet_preview['name']} — {message}")


def recompute_preview_can_import(preview: PreviewResult) -> None:
    preview.can_import = any(
        sheet["status"] == "recognized" and sheet["rows"] > 0 for sheet in preview.sheets
    )


def finalize_preview_can_import(preview: PreviewResult) -> None:
    preview.can_import = preview.can_import and not preview.errors


def append_preview_open_error(preview: PreviewResult, exc: Exception) -> None:
    preview.errors.append(f"Impossible d'ouvrir le fichier : {exc}")
