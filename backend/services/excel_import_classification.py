"""Worksheet classification helpers for historical Excel import."""

from __future__ import annotations

from typing import Any

from backend.services.excel_import_parsing import normalize_text


def sheet_has_content(ws: Any) -> bool:
    """Return True if the worksheet contains any non-empty cell."""
    for row in ws.iter_rows(values_only=True):
        if any(cell not in (None, "") for cell in row):
            return True
    return False


def classify_gestion_sheet(sheet_name: str) -> tuple[str | None, str | None]:
    """Classify a gestion worksheet into a supported import kind or ignore reason."""
    key = normalize_text(sheet_name)
    ignored_markers = (
        "aide",
        "todo",
        "depot",
        "montant total",
        "verification",
        "prevision",
        "bilan financier",
        "cdd",
        "salaire",
    )
    if any(marker in key for marker in ignored_markers):
        return None, "auxiliary-sheet"
    if any(marker in key for marker in ("fact", "client", "adh")):
        return "invoices", None
    if any(marker in key for marker in ("paie", "regl", "encaiss")):
        return "payments", None
    if any(marker in key for marker in ("contact", "fourniss")):
        return "contacts", None
    if any(marker in key for marker in ("caisse", "cash")):
        return "cash", None
    if any(marker in key for marker in ("banque", "bank", "relev")):
        return "bank", None
    return None, "unmapped-sheet"


def classify_comptabilite_sheet(sheet_name: str) -> tuple[str | None, str | None]:
    """Classify a comptabilite worksheet into a supported import kind or ignore reason."""
    key = normalize_text(sheet_name)
    if "saisie" in key:
        return None, "entry-helper-sheet"
    ignored_markers = (
        "donnees generales",
        "cle de repartition",
        "nomenclature",
        "grand livre",
        "balance",
        "etat factures",
        "extrait",
        "analytique",
        "bilan",
        "compte de resultat",
    )
    if any(marker in key for marker in ignored_markers):
        return None, "report-sheet"
    if key == "journal":
        return "entries", None
    if any(marker in key for marker in ("journal", "ecrit", "compta")):
        return "entries", None
    return None, "unmapped-sheet"
