#!/usr/bin/env python3
"""One-shot script: extract postal addresses from historical Word invoices
and enrich Contact.adresse.

Usage:
    python scripts/import_addresses_from_docx.py \\
        --source /path/to/docx/folder [--db data/solde.db] [--commit] [--verbose]

Default mode is --dry-run (no DB writes).  Pass --commit to actually update contacts.

Extraction logic:
  1. For each .docx file, find the invoice number (regex on paragraphs).
  2. Resolve the contact via Invoice.number in the database.
  3. Find the contact's name in the document paragraphs.
  4. Collect address lines that follow the contact name, up to a stop keyword
     (Objet, Référence, Facture, Date, N°, etc.).
  5. Sort all extractions by invoice date descending (most recent first).
  6. Keep only the first address found per contact (most recent address wins).
  7. In --commit mode: update Contact.adresse only when the field is NULL.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches invoice numbers like 2024-001, 2024-0045, FAC2025/012, FF-20241231...
_INVOICE_NUMBER_RE = re.compile(r"\b((?:FAC|FF-?)?\d{4}[-/]\d{2,4}(?:[-/]\d+)?|\d{4}[-/]\d{2,4})\b")

# Matches French date patterns: "01/04/2025", "1 avril 2025", "2025-04-01"
_DATE_RE = re.compile(
    r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b"
    r"|\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b"
    r"|\b(\d{1,2})\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})\b",
    re.IGNORECASE,
)

# Lines that signal the end of the address block
_STOP_KEYWORDS_RE = re.compile(
    r"^(objet|référence|ref\.|facture\s*n|date\s*:|n°\s*facture|doit\s*|bon\s*de\s*commande|tva|siret|rib\b|iban\b|bic\b)",
    re.IGNORECASE,
)
# "Metz, le 18 janvier 2025" or "Paris, le 01/04/2025" — city+date header, not an address line
_CITY_DATE_RE = re.compile(
    r"^[A-Za-z\u00C0-\u00FF][A-Za-z\u00C0-\u00FF\s-]+,\s*le\b",
    re.IGNORECASE,
)
_FRENCH_MONTHS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}

# Typical French postal code pattern (5 digits)
_POSTAL_CODE_RE = re.compile(r"\b\d{5}\b")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Extraction:
    file: Path
    invoice_number: str
    invoice_date: date | None
    contact_id: int
    contact_nom: str
    address: str


@dataclass
class Report:
    updated: list[tuple[int, str, str]] = field(default_factory=list)  # (id, nom, address)
    skipped_has_address: list[tuple[int, str]] = field(default_factory=list)  # (id, nom)
    skipped_no_address: list[tuple[int, str]] = field(default_factory=list)  # (contact_id, file)
    unresolved: list[tuple[str, Path]] = field(default_factory=list)  # (invoice_number, file)
    no_invoice_number: list[Path] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Docx helpers (python-docx)
# ---------------------------------------------------------------------------


def _require_docx() -> None:
    try:
        import docx  # noqa: F401
    except ImportError:
        print(
            "ERROR: python-docx is not installed.\nInstall it with:  pip install python-docx",
            file=sys.stderr,
        )
        sys.exit(1)


def _read_paragraphs(path: Path) -> list[str]:
    """Return non-empty paragraph texts from a .docx file."""
    from docx import Document  # noqa: PLC0415

    doc = Document(str(path))
    texts: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            texts.append(text)
    return texts


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------


def _extract_invoice_number(paragraphs: list[str]) -> str | None:
    """Return the first invoice-number-like token found in the paragraphs."""
    for para in paragraphs:
        m = _INVOICE_NUMBER_RE.search(para)
        if m:
            return m.group(0)
    return None


def _parse_date_from_paragraphs(paragraphs: list[str]) -> date | None:
    """Try to extract the invoice date from document text."""
    for para in paragraphs:
        m = _DATE_RE.search(para)
        if not m:
            continue
        try:
            groups = m.groups()
            if groups[0]:  # dd/mm/yyyy
                return date(int(groups[2]), int(groups[1]), int(groups[0]))
            if groups[3]:  # yyyy-mm-dd
                return date(int(groups[3]), int(groups[4]), int(groups[5]))
            if groups[6]:  # dd monthname yyyy
                day = int(groups[6])
                month_name = para.split()[
                    para.lower()
                    .split()
                    .index(next(w for w in para.lower().split() if w in _FRENCH_MONTHS))
                ]
                month = _FRENCH_MONTHS.get(month_name.lower(), 0)
                year = int(groups[7])
                if month:
                    return date(year, month, day)
        except (ValueError, StopIteration):
            continue
    return None


def _normalize(text: str) -> str:
    """Lower-case and remove accents for fuzzy matching."""
    replacements = {
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "à": "a",
        "â": "a",
        "ä": "a",
        "î": "i",
        "ï": "i",
        "ô": "o",
        "ö": "o",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
    }
    s = text.lower()
    for src, tgt in replacements.items():
        s = s.replace(src, tgt)
    return s


def _extract_address_block(
    paragraphs: list[str],
    contact_nom: str,
    contact_prenom: str | None,
    verbose: bool = False,
) -> str | None:
    """
    Find the contact name in the paragraphs, then collect lines after it
    until a stop keyword or an empty-equivalent line.
    Returns the joined address block, or None if not found.
    """
    norm_nom = _normalize(contact_nom)
    norm_prenom = _normalize(contact_prenom) if contact_prenom else None

    # Build a search key: "nom" or "prenom nom" or "nom prenom"
    search_keys: list[str] = [norm_nom]
    if norm_prenom:
        search_keys.append(f"{norm_prenom} {norm_nom}")
        search_keys.append(f"{norm_nom} {norm_prenom}")

    name_idx: int | None = None
    for idx, para in enumerate(paragraphs):
        norm_para = _normalize(para)
        if any(key in norm_para for key in search_keys):
            name_idx = idx
            break

    if name_idx is None:
        if verbose:
            print("    [address] Contact name not found in document paragraphs")
        return None

    if verbose:
        print(f"    [address] Found contact name at paragraph {name_idx}: {paragraphs[name_idx]!r}")

    # Collect lines after the name paragraph
    address_lines: list[str] = []
    for para in paragraphs[name_idx + 1 :]:
        if _STOP_KEYWORDS_RE.match(para):
            break
        # Stop at city+date header: "Metz, le 18 janvier 2025"
        if _CITY_DATE_RE.match(para):
            break
        # Stop if we see another invoice-number-like pattern that isn't part of address
        if _INVOICE_NUMBER_RE.match(para) and not _POSTAL_CODE_RE.search(para):
            break
        address_lines.append(para)
        # Stop collecting after we see a postal code (end of address)
        if _POSTAL_CODE_RE.search(para):
            break

    if not address_lines:
        if verbose:
            print("    [address] No address lines found after contact name")
        return None

    address = "\n".join(address_lines)
    # Sanity check: a French postal address must contain a 5-digit postal code
    if not _POSTAL_CODE_RE.search(address):
        if verbose:
            print(f"    [address] Rejected (no postal code): {address!r}")
        return None

    if verbose:
        print(f"    [address] Extracted: {address!r}")
    return address


# ---------------------------------------------------------------------------
# Database helpers (sync sqlite3)
# ---------------------------------------------------------------------------


def _db_connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_contact_by_invoice_number(
    conn: sqlite3.Connection,
    invoice_number: str,
) -> tuple[int, str, str | None, str | None] | None:
    """Return (contact_id, nom, prenom, current_adresse) or None."""
    row = conn.execute(
        """
        SELECT c.id, c.nom, c.prenom, c.adresse
        FROM invoices i
        JOIN contacts c ON c.id = i.contact_id
        WHERE i.number = ? AND i.type = 'client'
        LIMIT 1
        """,
        (invoice_number,),
    ).fetchone()
    if row is None:
        return None
    return (row["id"], row["nom"], row["prenom"], row["adresse"])


def _update_contact_address(
    conn: sqlite3.Connection,
    contact_id: int,
    address: str,
) -> None:
    conn.execute(
        "UPDATE contacts SET adresse = ? WHERE id = ? AND adresse IS NULL",
        (address, contact_id),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------


def _process_file(
    path: Path,
    conn: sqlite3.Connection,
    verbose: bool,
) -> tuple[Extraction | None, str | None]:
    """
    Process one .docx file.
    Returns (Extraction, None) on success or (None, error_message) on failure.
    """
    if verbose:
        print(f"\n  Processing: {path.name}")

    try:
        paragraphs = _read_paragraphs(path)
    except Exception as exc:
        return None, f"Could not read file: {exc}"

    invoice_number = _extract_invoice_number(paragraphs)
    if not invoice_number:
        return None, "no_invoice_number"

    if verbose:
        print(f"    Invoice number: {invoice_number}")

    invoice_date = _parse_date_from_paragraphs(paragraphs)
    if verbose:
        print(f"    Invoice date: {invoice_date}")

    contact_row = _resolve_contact_by_invoice_number(conn, invoice_number)
    if contact_row is None:
        return None, f"unresolved:{invoice_number}"

    contact_id, nom, prenom, _ = contact_row
    if verbose:
        print(f"    Contact: #{contact_id} {nom} {prenom or ''}")

    address = _extract_address_block(paragraphs, nom, prenom, verbose=verbose)
    if address is None:
        return None, f"no_address:{contact_id}"

    return Extraction(
        file=path,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        contact_id=contact_id,
        contact_nom=f"{nom} {prenom or ''}".strip(),
        address=address,
    ), None


def run(
    source_dir: Path,
    db_path: Path,
    commit: bool,
    verbose: bool,
) -> None:
    _require_docx()

    docx_files = sorted(source_dir.glob("*.docx"))
    if not docx_files:
        print(f"No .docx files found in {source_dir}")
        return

    print(f"Found {len(docx_files)} .docx file(s) in {source_dir}")
    print(f"Database: {db_path}")
    print(f"Mode: {'COMMIT' if commit else 'DRY-RUN (pass --commit to apply)'}")

    conn = _db_connect(db_path)
    report = Report()

    extractions: list[Extraction] = []

    for path in docx_files:
        ext, error = _process_file(path, conn, verbose)
        if ext is not None:
            extractions.append(ext)
        elif error == "no_invoice_number":
            report.no_invoice_number.append(path)
            if verbose:
                print("    >> SKIP: no invoice number found")
        elif error and error.startswith("unresolved:"):
            inv_num = error.split(":", 1)[1]
            report.unresolved.append((inv_num, path))
            if verbose:
                print(f"    >> SKIP: invoice {inv_num!r} not found in DB")
        elif error and error.startswith("no_address:"):
            cid = int(error.split(":", 1)[1])
            row = conn.execute("SELECT nom, prenom FROM contacts WHERE id=?", (cid,)).fetchone()
            nom_str = f"{row['nom']} {row['prenom'] or ''}".strip() if row else str(cid)
            report.skipped_no_address.append((cid, path.name))
            if verbose:
                print(f"    >> SKIP: could not extract address for contact #{cid} {nom_str}")
        else:
            if verbose:
                print(f"    >> SKIP: {error}")

    # Sort by date descending - most recent first
    extractions.sort(
        key=lambda e: e.invoice_date or date.min,
        reverse=True,
    )

    # Keep only the most recent extraction per contact
    seen_contacts: set[int] = set()
    for ext in extractions:
        if ext.contact_id in seen_contacts:
            continue
        seen_contacts.add(ext.contact_id)

        # Check current DB state
        row = conn.execute(
            "SELECT adresse FROM contacts WHERE id = ?", (ext.contact_id,)
        ).fetchone()
        if row is None:
            continue

        current_adresse = row["adresse"]

        if current_adresse is not None:
            report.skipped_has_address.append((ext.contact_id, ext.contact_nom))
            if verbose:
                print(
                    f"\n  [{ext.file.name}] Contact #{ext.contact_id} {ext.contact_nom}: "
                    f"already has address -- skip"
                )
            continue

        report.updated.append((ext.contact_id, ext.contact_nom, ext.address))
        if commit:
            _update_contact_address(conn, ext.contact_id, ext.address)
            print(
                f"  [OK] Updated  #{ext.contact_id} {ext.contact_nom}: "
                f"{ext.address[:60].replace(chr(10), ' / ')!r}"
            )
        else:
            print(
                f"  [--] Would update #{ext.contact_id} {ext.contact_nom}: "
                f"{ext.address[:60].replace(chr(10), ' / ')!r}"
            )

    conn.close()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Files processed         : {len(docx_files)}")
    print(f"  Would update / updated  : {len(report.updated)}")
    print(f"  Skipped (has address)   : {len(report.skipped_has_address)}")
    print(f"  Skipped (no addr found) : {len(report.skipped_no_address)}")
    print(f"  Unresolved (not in DB)  : {len(report.unresolved)}")
    print(f"  No invoice number found : {len(report.no_invoice_number)}")

    if report.unresolved:
        print("\nUnresolved invoice numbers:")
        for inv_num, path in report.unresolved:
            print(f"  {path.name}: invoice {inv_num!r}")

    if report.no_invoice_number:
        print("\nFiles with no invoice number:")
        for path in report.no_invoice_number:
            print(f"  {path.name}")

    if not commit and report.updated:
        print(
            f"\nDRY-RUN: {len(report.updated)} contact(s) would be updated."
            " Re-run with --commit to apply."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract postal addresses from Word invoices and update Contact.adresse."
    )
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Folder containing .docx invoice files",
    )
    parser.add_argument(
        "--db",
        default=Path("data/solde.db"),
        type=Path,
        help="Path to the SQLite database (default: data/solde.db)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write to the database (default: dry-run)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show extraction details for each file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(
        source_dir=args.source,
        db_path=args.db,
        commit=args.commit,
        verbose=args.verbose,
    )
