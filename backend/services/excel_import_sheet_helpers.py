"""Worksheet structure helpers for historical Excel import."""

from __future__ import annotations

from typing import Any

from backend.services.excel_import_parsing import normalize_text, parse_str


def find_col_idx(col_map: dict[str, int], *fragments: str) -> int | None:
    """Find the first column whose normalized label contains one fragment."""
    normalized_fragments = [normalize_text(fragment) for fragment in fragments]
    for key, idx in col_map.items():
        normalized_key = normalize_text(key)
        if any(fragment in normalized_key for fragment in normalized_fragments):
            return idx
    return None


def find_invoice_number_idx(
    col_map: dict[str, int], *, exclude_idx: int | None
) -> int | None:
    """Find the invoice number/reference column while avoiding false positives."""
    for key, idx in col_map.items():
        if exclude_idx is not None and idx == exclude_idx:
            continue
        normalized_key = normalize_text(key)
        if any(
            fragment in normalized_key
            for fragment in ("ref facture", "reference", "facture", "numero", "num")
        ) and "etat" not in normalized_key and "montant" not in normalized_key:
            return idx
    return None


def detect_header_row(ws: Any, keywords: list[str]) -> tuple[int, dict[str, int]] | None:
    """Find the header row and return the normalized column map."""
    normalized_keywords = [normalize_text(keyword) for keyword in keywords]
    for row_idx, row in enumerate(ws.iter_rows(max_row=20, values_only=True), start=1):
        row_lower = [normalize_text(parse_str(cell)) for cell in row]
        matched = sum(
            1 for keyword in normalized_keywords if any(keyword in cell for cell in row_lower)
        )
        if matched >= 2:
            return row_idx, {cell: col_idx for col_idx, cell in enumerate(row_lower)}
    return None


def get_row_value(row: tuple[Any, ...], idx: int | None) -> Any:
    """Safely read a row value by column index."""
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def row_text_values(row: tuple[Any, ...]) -> list[str]:
    """Return normalized non-empty textual values for a source row."""
    values: list[str] = []
    for cell in row:
        text = normalize_text(parse_str(cell))
        if text:
            values.append(text)
    return values


def row_contains_text(row: tuple[Any, ...], *fragments: str) -> bool:
    """Return True when one normalized row cell contains a fragment."""
    normalized_fragments = [normalize_text(fragment) for fragment in fragments]
    return any(
        fragment in cell for cell in row_text_values(row) for fragment in normalized_fragments
    )


def compose_description(*values: Any) -> str:
    """Join non-empty textual values into a compact import description."""
    parts: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = parse_str(value, max_len=500)
        normalized = normalize_text(text)
        if not text or normalized in seen:
            continue
        seen.add(normalized)
        parts.append(text)
    return " ; ".join(parts)