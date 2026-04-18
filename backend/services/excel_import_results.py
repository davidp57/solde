"""Result containers for historical Excel import preview and execution."""

from __future__ import annotations

import re
from typing import Any

from backend.services.excel_import_policy import issue_category_for_message

_SHEET_PREFIX_SEPARATOR = " — "
_ROW_ISSUE_RE = re.compile(r"^Ligne (?P<row_number>\d+) : (?P<message>.+)$")
_EXISTING_IN_SOLDE_CATEGORIES = {
    "existing-contact",
    "existing-invoice",
    "existing-salary",
}


def _split_sheet_prefix(message: str) -> tuple[str | None, str]:
    if _SHEET_PREFIX_SEPARATOR not in message:
        return None, message
    sheet_name, stripped_message = message.split(_SHEET_PREFIX_SEPARATOR, 1)
    return sheet_name, stripped_message


def _split_row_issue(message: str) -> tuple[int | None, str]:
    match = _ROW_ISSUE_RE.match(message)
    if match is None:
        return None, message
    return int(match.group("row_number")), match.group("message")


def _make_issue_detail(
    *,
    raw_message: str,
    severity: str,
    sheet_name: str | None = None,
    kind: str | None = None,
) -> dict[str, Any]:
    resolved_sheet_name = sheet_name
    scoped_message = raw_message
    if resolved_sheet_name is None:
        resolved_sheet_name, scoped_message = _split_sheet_prefix(raw_message)

    row_number, message = _split_row_issue(scoped_message)
    return {
        "category": issue_category_for_message(
            message,
            kind=kind,
            row_number=row_number,
            severity=severity,
        ),
        "severity": severity,
        "sheet_name": resolved_sheet_name,
        "kind": kind,
        "row_number": row_number,
        "message": message,
        "display_message": raw_message,
    }


def _serialize_issue_details(
    messages: list[str],
    *,
    severity: str,
    sheet_name: str | None = None,
    kind: str | None = None,
    kind_by_sheet_name: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for raw_message in messages:
        detail = _make_issue_detail(
            raw_message=raw_message,
            severity=severity,
            sheet_name=sheet_name,
            kind=kind,
        )
        if detail["sheet_name"] and detail["kind"] is None and kind_by_sheet_name is not None:
            detail["kind"] = kind_by_sheet_name.get(detail["sheet_name"])
            detail["category"] = issue_category_for_message(
                detail["message"],
                kind=detail["kind"],
                row_number=detail["row_number"],
                severity=severity,
            )
        details.append(detail)
    return details


def _serialize_sheet_summary(summary: dict[str, Any]) -> dict[str, Any]:
    serialized = dict(summary)
    serialized["warning_details"] = _serialize_issue_details(
        list(summary.get("warnings", [])),
        severity="warning",
        sheet_name=summary.get("name"),
        kind=summary.get("kind"),
    )
    serialized["error_details"] = _serialize_issue_details(
        list(summary.get("errors", [])),
        severity="error",
        sheet_name=summary.get("name"),
        kind=summary.get("kind"),
    )
    return serialized


def _build_gestion_preview_comparison(
    serialized_sheets: list[dict[str, Any]],
    *,
    extra_in_solde_by_kind: dict[str, int] | None = None,
) -> dict[str, Any]:
    extra_in_solde_by_kind = extra_in_solde_by_kind or {}
    domains: list[dict[str, Any]] = []
    for summary in serialized_sheets:
        kind = summary.get("kind")
        if kind in (None, "ignored", "entries"):
            continue
        if summary.get("status") not in {"recognized", "unsupported"}:
            continue

        policy_ignored_rows = int(summary.get("policy_ignored_rows", 0))
        ignored_rows = int(summary.get("ignored_rows", 0))
        source_rows = int(summary.get("source_rows", summary.get("rows", 0)))
        initial_blocked_rows = int(summary.get("initial_blocked_rows", 0))
        domain = {
            "kind": kind,
            "file_rows": source_rows + policy_ignored_rows + initial_blocked_rows,
            "already_in_solde": max(0, ignored_rows - policy_ignored_rows),
            "missing_in_solde": int(summary.get("rows", 0)),
            "extra_in_solde": int(extra_in_solde_by_kind.get(str(kind), 0)),
            "ignored_by_policy": policy_ignored_rows,
            "blocked": int(summary.get("blocked_rows", 0)),
        }
        domains.append(domain)

    return {
        "mode": "gestion-excel-to-solde",
        "direction": "excel-to-solde",
        "domains": domains,
        "totals": {
            "file_rows": sum(domain["file_rows"] for domain in domains),
            "already_in_solde": sum(domain["already_in_solde"] for domain in domains),
            "missing_in_solde": sum(domain["missing_in_solde"] for domain in domains),
            "extra_in_solde": sum(domain["extra_in_solde"] for domain in domains),
            "ignored_by_policy": sum(domain["ignored_by_policy"] for domain in domains),
            "blocked": sum(domain["blocked"] for domain in domains),
        },
    }


def _build_comptabilite_preview_comparison(
    serialized_sheets: list[dict[str, Any]],
    *,
    extra_in_solde_by_kind: dict[str, int] | None = None,
) -> dict[str, Any]:
    extra_in_solde_by_kind = extra_in_solde_by_kind or {}
    domains: list[dict[str, Any]] = []
    for summary in serialized_sheets:
        kind = summary.get("kind")
        if kind != "entries":
            continue
        if summary.get("status") not in {"recognized", "unsupported"}:
            continue

        policy_ignored_rows = int(summary.get("policy_ignored_rows", 0))
        ignored_rows = int(summary.get("ignored_rows", 0))
        source_rows = int(summary.get("source_rows", summary.get("rows", 0)))
        initial_blocked_rows = int(summary.get("initial_blocked_rows", 0))
        domains.append(
            {
                "kind": kind,
                "file_rows": source_rows + policy_ignored_rows + initial_blocked_rows,
                "already_in_solde": max(0, ignored_rows - policy_ignored_rows),
                "missing_in_solde": int(summary.get("rows", 0)),
                "extra_in_solde": int(extra_in_solde_by_kind.get("entries", 0)),
                "ignored_by_policy": policy_ignored_rows,
                "blocked": int(summary.get("blocked_rows", 0)),
            }
        )

    return {
        "mode": "global-convergence",
        "direction": "bidirectional",
        "domains": domains,
        "totals": {
            "file_rows": sum(domain["file_rows"] for domain in domains),
            "already_in_solde": sum(domain["already_in_solde"] for domain in domains),
            "missing_in_solde": sum(domain["missing_in_solde"] for domain in domains),
            "extra_in_solde": sum(domain["extra_in_solde"] for domain in domains),
            "ignored_by_policy": sum(domain["ignored_by_policy"] for domain in domains),
            "blocked": sum(domain["blocked"] for domain in domains),
        },
    }


class ImportResult:
    """Summary of an import operation."""

    def __init__(self) -> None:
        self.contacts_created: int = 0
        self.invoices_created: int = 0
        self.payments_created: int = 0
        self.salaries_created: int = 0
        self.entries_created: int = 0
        self.cash_created: int = 0
        self.bank_created: int = 0
        self.skipped: int = 0
        self.ignored_rows: int = 0
        self.blocked_rows: int = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.sheets: list[dict[str, Any]] = []
        self._sheet_index: dict[tuple[str, str], dict[str, Any]] = {}
        self._created_objects: list[dict[str, Any]] = []

    def to_dict(self) -> dict[str, Any]:
        serialized_sheets = [_serialize_sheet_summary(summary) for summary in self.sheets]
        kind_by_sheet_name = {
            summary["name"]: summary["kind"]
            for summary in serialized_sheets
            if summary.get("name") and summary.get("kind")
        }
        return {
            "contacts_created": self.contacts_created,
            "invoices_created": self.invoices_created,
            "payments_created": self.payments_created,
            "salaries_created": self.salaries_created,
            "entries_created": self.entries_created,
            "cash_created": self.cash_created,
            "bank_created": self.bank_created,
            "skipped": self.skipped,
            "ignored_rows": self.ignored_rows,
            "blocked_rows": self.blocked_rows,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_details": _serialize_issue_details(
                self.errors,
                severity="error",
                kind_by_sheet_name=kind_by_sheet_name,
            ),
            "warning_details": _serialize_issue_details(
                self.warnings,
                severity="warning",
                kind_by_sheet_name=kind_by_sheet_name,
            ),
            "sheets": serialized_sheets,
        }

    def to_log_dict(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload["created_objects"] = list(self._created_objects)
        return payload

    def _ensure_sheet_summary(self, sheet_name: str, kind: str) -> dict[str, Any]:
        key = (sheet_name, kind)
        if key not in self._sheet_index:
            summary = {
                "name": sheet_name,
                "kind": kind,
                "imported_rows": 0,
                "ignored_rows": 0,
                "blocked_rows": 0,
                "warnings": [],
                "errors": [],
            }
            self._sheet_index[key] = summary
            self.sheets.append(summary)
        return self._sheet_index[key]

    def add_imported_row(self, sheet_name: str, kind: str, count: int = 1) -> None:
        self._ensure_sheet_summary(sheet_name, kind)["imported_rows"] += count

    def add_ignored_row(self, sheet_name: str, kind: str, message: str) -> None:
        self.skipped += 1
        self.ignored_rows += 1
        summary = self._ensure_sheet_summary(sheet_name, kind)
        summary["ignored_rows"] += 1
        summary["warnings"].append(message)
        self.warnings.append(f"{sheet_name} — {message}")

    def add_blocked_row(self, sheet_name: str, kind: str, message: str) -> None:
        self.blocked_rows += 1
        summary = self._ensure_sheet_summary(sheet_name, kind)
        summary["blocked_rows"] += 1
        summary["errors"].append(message)
        self.errors.append(f"{sheet_name} — {message}")

    def add_warning(self, sheet_name: str, kind: str, message: str) -> None:
        summary = self._ensure_sheet_summary(sheet_name, kind)
        summary["warnings"].append(message)
        self.warnings.append(f"{sheet_name} — {message}")

    def add_open_file_error(self, exc: Exception) -> None:
        self.errors.append(f"Impossible d'ouvrir le fichier : {exc}")

    def add_import_error(self, scope: str, exc: Exception) -> None:
        self.errors.append(f"Erreur import {scope} : {exc}")

    def record_created_object(
        self,
        *,
        sheet_name: str,
        kind: str,
        object_type: str,
        object_id: int | None,
        reference: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._created_objects.append(
            {
                "sheet_name": sheet_name,
                "kind": kind,
                "object_type": object_type,
                "object_id": object_id,
                "reference": reference,
                "details": details or {},
            }
        )

    def absorb_preview(self, preview: PreviewResult) -> None:
        self.blocked_rows = sum(sheet.get("blocked_rows", 0) for sheet in preview.sheets)
        self.ignored_rows = sum(sheet.get("ignored_rows", 0) for sheet in preview.sheets)
        self.skipped = self.ignored_rows
        self.errors.extend(preview.errors)
        self.warnings.extend(preview.warnings)
        for sheet in preview.sheets:
            summary = self._ensure_sheet_summary(sheet["name"], sheet["kind"])
            summary["ignored_rows"] = sheet.get("ignored_rows", 0)
            summary["blocked_rows"] = sheet.get("blocked_rows", 0)
            summary["warnings"] = list(sheet.get("warnings", []))
            summary["errors"] = list(sheet.get("errors", []))

    def reset_persisted_counts(self) -> None:
        """Reset counters when a global rollback cancels all pending writes."""
        self.contacts_created = 0
        self.invoices_created = 0
        self.payments_created = 0
        self.salaries_created = 0
        self.entries_created = 0
        self.cash_created = 0
        self.bank_created = 0
        self._created_objects.clear()
        for summary in self.sheets:
            summary["imported_rows"] = 0


class PreviewResult:
    """Dry-run parse summary with detailed sheet diagnostics."""

    def __init__(self) -> None:
        self.sheets: list[dict[str, Any]] = []
        self.estimated_contacts: int = 0
        self.estimated_invoices: int = 0
        self.estimated_payments: int = 0
        self.estimated_salaries: int = 0
        self.estimated_entries: int = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.sample_rows: list[dict[str, Any]] = []
        self.can_import: bool = False
        self._candidate_contacts: set[str] = set()
        self.comparison_mode: str | None = None
        self.comparison_context: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        serialized_sheets = [_serialize_sheet_summary(summary) for summary in self.sheets]
        kind_by_sheet_name = {
            summary["name"]: summary["kind"]
            for summary in serialized_sheets
            if summary.get("name") and summary.get("kind")
        }
        payload = {
            "sheets": serialized_sheets,
            "estimated_contacts": self.estimated_contacts,
            "estimated_invoices": self.estimated_invoices,
            "estimated_payments": self.estimated_payments,
            "estimated_salaries": self.estimated_salaries,
            "estimated_entries": self.estimated_entries,
            "sample_rows": self.sample_rows,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_details": _serialize_issue_details(
                self.errors,
                severity="error",
                kind_by_sheet_name=kind_by_sheet_name,
            ),
            "warning_details": _serialize_issue_details(
                self.warnings,
                severity="warning",
                kind_by_sheet_name=kind_by_sheet_name,
            ),
            "can_import": self.can_import,
        }
        if self.comparison_mode == "gestion-excel-to-solde":
            payload["comparison"] = _build_gestion_preview_comparison(
                serialized_sheets,
                extra_in_solde_by_kind=self.comparison_context.get("extra_in_solde_by_kind"),
            )
        if self.comparison_mode == "global-convergence":
            payload["comparison"] = _build_comptabilite_preview_comparison(
                serialized_sheets,
                extra_in_solde_by_kind=self.comparison_context.get("extra_in_solde_by_kind"),
            )
        return payload
