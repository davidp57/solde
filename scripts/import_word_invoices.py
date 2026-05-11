#!/usr/bin/env python3
"""Import historical client invoices from Word (.docx) files into Solde.

For each .docx file (pattern: "facture YYYY-NNNN.docx"):
  - Extract the invoice number from the filename.
  - Parse date, client name, address, and line items from the document.
  - Skip the file if an invoice with that number already exists in the DB.
  - Find or create the client contact.
  - Create the invoice with status=ARCHIVED (no accounting entries).
  - Copy the .docx file to data/uploads/invoices/ and store the path.

Usage:
    python scripts/import_word_invoices.py \\
        --source /path/to/docx/folder [--db data/solde.db] [--commit] [--verbose]

Default mode is dry-run (no DB writes). Pass --commit to write to the database.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches "facture YYYY-NNNN.docx" → captures "YYYY-NNNN"
_FILENAME_RE = re.compile(r"^facture\s+(\d{4}-\d{4})\.docx$", re.IGNORECASE)

# Matches French date patterns: "01/04/2025", "1 avril 2025", "2025-04-01"
_DATE_RE = re.compile(
    r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b"
    r"|\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b"
    r"|\b(\d{1,2})\s+(janvier|f[eé]vrier|mars|avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|d[eé]cembre)\s+(\d{4})\b",
    re.IGNORECASE,
)

_FRENCH_MONTHS = {
    "janvier": 1,
    "fevrier": 2,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
    "décembre": 12,
}

# Header/footer paragraphs to skip when looking for client name
_SKIP_PARAGRAPHS_RE = re.compile(
    r"^(les[\s\xa0]+etudes|metz,?\s+le\s|facture\s*n|en\s+votre|par\s+virement|bic\s*:|par\s+ch[eè]que|en\s+esp[eè]ces|r[eè]glement|pr[eé]cisez|pay[eé]|iban|rib\b)",
    re.IGNORECASE,
)

# Price pattern: "26,00€" or "26.00" or "130 €"
_PRICE_RE = re.compile(r"([\d\s]+[,.][\d]+)\s*€?")

# Total row marker
_TOTAL_RE = re.compile(r"^total\s*$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class InvoiceLine:
    description: str
    amount: Decimal


@dataclass
class ParsedInvoice:
    number: str
    file: Path
    invoice_date: date | None
    client_name: str | None
    client_address: str | None
    lines: list[InvoiceLine]
    total_amount: Decimal


@dataclass
class ImportReport:
    created: list[str] = field(default_factory=list)
    skipped_exists: list[str] = field(default_factory=list)
    skipped_no_client: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_docx() -> None:
    try:
        import docx  # noqa: F401
    except ImportError:
        print("ERROR: python-docx not installed. Run: pip install python-docx", file=sys.stderr)
        sys.exit(1)


def _normalize_name(text: str) -> str:
    """Lower-case, strip accents for fuzzy matching."""
    result = text.lower()
    for src, tgt in {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ù": "u", "û": "u", "ü": "u",
        "ç": "c",
    }.items():
        result = result.replace(src, tgt)
    return result


def _parse_price(text: str) -> Decimal | None:
    """Parse a price string like '26,00€' or '130 €' into a Decimal."""
    clean = text.replace("\xa0", "").replace(" ", "").replace("€", "").strip()
    clean = clean.replace(",", ".")
    try:
        return Decimal(clean).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _parse_date(text: str) -> date | None:
    """Extract a date from a text string."""
    m = _DATE_RE.search(text)
    if not m:
        return None
    groups = m.groups()
    try:
        if groups[0]:  # dd/mm/yyyy
            return date(int(groups[2]), int(groups[1]), int(groups[0]))
        if groups[3]:  # yyyy-mm-dd
            return date(int(groups[3]), int(groups[4]), int(groups[5]))
        if groups[6]:  # dd monthname yyyy
            day = int(groups[6])
            month = _FRENCH_MONTHS.get(_normalize_name(groups[7]), 0)
            year = int(groups[8])
            if month:
                return date(year, month, day)
    except (ValueError, TypeError):
        pass
    return None


# ---------------------------------------------------------------------------
# Document parsing
# ---------------------------------------------------------------------------


def _get_paragraphs(path: Path) -> list[str]:
    from docx import Document  # noqa: PLC0415

    doc = Document(str(path))
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]


def _get_tables(path: Path) -> list[list[list[str]]]:
    """Return all tables as list[rows[cells]]."""
    from docx import Document  # noqa: PLC0415

    doc = Document(str(path))
    result = []
    for table in doc.tables:
        rows = []
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            rows.append(cells)
        result.append(rows)
    return result


def _extract_client_block(paragraphs: list[str]) -> tuple[str | None, str | None]:
    """
    Extract client name and address from document paragraphs.

    The structure of these invoices is:
      [0] "LES ETUDES"                 ← header (skip)
      [4] "PRENOM NOM"                 ← client name
      [5] "street address"             ← address line 1
      [6] "POSTAL_CODE CITY"           ← address line 2
      [10] "Metz, le DD mois YYYY"     ← date (skip)
    """
    postal_re = re.compile(r"\b\d{5}\b")
    client_name: str | None = None
    address_lines: list[str] = []

    for para in paragraphs:
        # Skip known header/footer content
        if _SKIP_PARAGRAPHS_RE.match(para):
            continue
        # Skip city+date header line (e.g. "Metz, le 18 janvier 2025")
        if re.match(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]+,\s*le\s+", para, re.IGNORECASE):
            continue
        # Stop at "Facture n°" line
        if re.match(r"^facture\s*n", para, re.IGNORECASE):
            break

        if client_name is None:
            client_name = para
        else:
            address_lines.append(para)
            # Stop after postal code line
            if postal_re.search(para):
                break

    address = "\n".join(address_lines) if address_lines else None
    return client_name, address


def _extract_lines_and_total(tables: list[list[list[str]]]) -> tuple[list[InvoiceLine], Decimal]:
    """
    Parse invoice lines from tables.
    Expected format: 2-column table (description | price), last row = Total.
    """
    lines: list[InvoiceLine] = []
    total = Decimal("0.00")

    for table_rows in tables:
        for row in table_rows:
            if len(row) < 2:
                continue
            desc = row[0].strip()
            price_text = row[-1].strip()  # last column is always amount

            price = _parse_price(price_text)
            if price is None:
                continue

            if _TOTAL_RE.match(desc):
                total = price
            else:
                lines.append(InvoiceLine(description=desc, amount=price))

    # If total not found from table, sum lines
    if total == Decimal("0.00") and lines:
        total = sum((ln.amount for ln in lines), Decimal("0.00"))

    return lines, total


def parse_docx(path: Path) -> ParsedInvoice | None:
    """Parse a .docx invoice file and return structured data, or None on failure."""
    m = _FILENAME_RE.match(path.name)
    if not m:
        return None
    number = m.group(1)

    try:
        paragraphs = _get_paragraphs(path)
        tables = _get_tables(path)
    except Exception:
        return None

    # Extract date from any paragraph containing a date pattern
    invoice_date: date | None = None
    for para in paragraphs:
        d = _parse_date(para)
        if d:
            invoice_date = d
            break

    client_name, client_address = _extract_client_block(paragraphs)
    lines, total = _extract_lines_and_total(tables)

    return ParsedInvoice(
        number=number,
        file=path,
        invoice_date=invoice_date,
        client_name=client_name,
        client_address=client_address,
        lines=lines,
        total_amount=total,
    )


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


def _invoice_exists(conn: sqlite3.Connection, number: str) -> bool:
    row = conn.execute("SELECT 1 FROM invoices WHERE number = ?", (number,)).fetchone()
    return row is not None


def _find_contact(conn: sqlite3.Connection, client_name: str) -> int | None:
    """Find a contact by name (case-insensitive, both 'NOM PRENOM' and 'PRENOM NOM' order)."""
    norm = _normalize_name(client_name)
    rows = conn.execute(
        "SELECT id, nom, prenom FROM contacts WHERE type = 'client'",
    ).fetchall()
    for row in rows:
        nom_full = _normalize_name(f"{row['nom']} {row['prenom'] or ''}").strip()
        prenom_nom = _normalize_name(f"{row['prenom'] or ''} {row['nom']}").strip()
        if norm in (nom_full, prenom_nom):
            return row["id"]
    return None


def _split_name(full_name: str) -> tuple[str, str | None]:
    """
    Split 'PRENOM NOM' into (nom, prenom).
    Convention: last word = nom, rest = prenom.
    Applies title-case.
    """
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0].title(), None
    nom = parts[-1].title()
    prenom = " ".join(parts[:-1]).title()
    return nom, prenom


def _create_contact(
    conn: sqlite3.Connection,
    client_name: str,
    address: str | None,
) -> int:
    """Insert a new CLIENT contact and return its id."""
    nom, prenom = _split_name(client_name)
    conn.execute(
        """
        INSERT INTO contacts (type, nom, prenom, adresse, is_active, blocked, created_at, updated_at)
        VALUES ('client', ?, ?, ?, 1, 0, datetime('now'), datetime('now'))
        """,
        (nom, prenom, address),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def _get_next_invoice_seq(conn: sqlite3.Connection, year: int) -> int:
    """Return the next available client invoice sequence number for the given year."""
    prefix = f"{year}-"
    row = conn.execute(
        """
        SELECT number FROM invoices
        WHERE type = 'client' AND number LIKE ?
        ORDER BY number DESC LIMIT 1
        """,
        (f"{prefix}%",),
    ).fetchone()
    if row is None:
        return 1
    last = row["number"]
    try:
        return int(last.split("-")[-1]) + 1
    except (ValueError, IndexError):
        return 1


def _create_invoice(
    conn: sqlite3.Connection,
    parsed: ParsedInvoice,
    contact_id: int,
    file_path: str,
) -> int:
    """Insert the invoice and its lines. Returns the new invoice id."""
    invoice_date = parsed.invoice_date or date.today()
    number = parsed.number

    conn.execute(
        """
        INSERT INTO invoices (
            number, type, contact_id, date, status, total_amount, paid_amount,
            has_explicit_breakdown, pdf_path, file_path, created_at, updated_at
        ) VALUES (?, 'client', ?, ?, 'archived', ?, 0, ?, NULL, ?, datetime('now'), datetime('now'))
        """,
        (
            number,
            contact_id,
            invoice_date.isoformat(),
            str(parsed.total_amount),
            1 if len(parsed.lines) > 1 else 0,
            file_path,
        ),
    )
    invoice_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    for ln in parsed.lines:
        conn.execute(
            """
            INSERT INTO invoice_lines (invoice_id, description, line_type, quantity, unit_price, amount)
            VALUES (?, ?, 'autres', 1, ?, ?)
            """,
            (invoice_id, ln.description, str(ln.amount), str(ln.amount)),
        )

    return invoice_id


def _copy_docx(src: Path, upload_dir: Path, dry_run: bool) -> str:
    """Copy the .docx to the uploads directory. Returns the relative filename."""
    safe_name = f"{uuid.uuid4().hex}.docx"
    dest = upload_dir / safe_name
    if not dry_run:
        upload_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return safe_name


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import historical Word invoices into Solde (dry-run by default)."
    )
    parser.add_argument("--source", required=True, help="Path to folder containing .docx files")
    parser.add_argument("--db", default="data/solde.db", help="Path to SQLite database")
    parser.add_argument("--commit", action="store_true", help="Write changes to DB (default: dry-run)")
    parser.add_argument("--verbose", action="store_true", help="Print detailed info per file")
    args = parser.parse_args()

    _require_docx()

    source = Path(args.source)
    if not source.is_dir():
        print(f"ERROR: Source folder not found: {source}", file=sys.stderr)
        sys.exit(1)

    db_path = Path(args.db)
    upload_dir = Path("data/uploads/invoices").resolve()
    dry_run = not args.commit

    if dry_run:
        print("DRY-RUN mode — no changes will be made. Pass --commit to write to DB.\n")

    conn = _db_connect(db_path)
    report = ImportReport()

    docx_files = sorted(source.glob("*.docx"))
    print(f"Found {len(docx_files)} .docx file(s) in {source}\n")

    for docx_file in docx_files:
        if args.verbose:
            print(f"Processing: {docx_file.name}")

        parsed = parse_docx(docx_file)
        if parsed is None:
            if args.verbose:
                print(f"  -> Skipped (name does not match pattern)")
            continue

        # Skip if already in DB
        if _invoice_exists(conn, parsed.number):
            report.skipped_exists.append(parsed.number)
            if args.verbose:
                print(f"  -> Skipped: invoice {parsed.number} already exists")
            continue

        # Resolve or create contact
        if parsed.client_name is None:
            report.skipped_no_client.append(parsed.number)
            if args.verbose:
                print(f"  -> Skipped: could not extract client name")
            continue

        contact_id = _find_contact(conn, parsed.client_name)
        created_contact = False
        if contact_id is None:
            if dry_run:
                contact_id = -1
            else:
                contact_id = _create_contact(conn, parsed.client_name, parsed.client_address)
            created_contact = True

        if args.verbose:
            action = "would create" if dry_run else "created"
            contact_info = f"contact #{contact_id}" if not created_contact else f"{'would create' if dry_run else 'new'} contact for '{parsed.client_name}'"
            print(f"  -> Date: {parsed.invoice_date}  Client: {parsed.client_name}  "
                  f"Total: {parsed.total_amount}€  Lines: {len(parsed.lines)}  "
                  f"Contact: {contact_info}")

        # Copy .docx
        file_path = _copy_docx(docx_file, upload_dir, dry_run)

        # Create invoice
        if not dry_run:
            try:
                _create_invoice(conn, parsed, contact_id, file_path)
                conn.commit()
                report.created.append(parsed.number)
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                report.errors.append((parsed.number, str(exc)))
                if args.verbose:
                    print(f"  -> ERROR: {exc}")
        else:
            report.created.append(parsed.number)

    conn.close()

    # Summary
    print(f"\n{'=' * 60}")
    print(f"{'DRY-RUN ' if dry_run else ''}IMPORT REPORT")
    print(f"{'=' * 60}")
    print(f"  {'Would create' if dry_run else 'Created'}  : {len(report.created)} invoice(s)")
    print(f"  Skipped (already exists)  : {len(report.skipped_exists)}")
    print(f"  Skipped (no client name)  : {len(report.skipped_no_client)}")
    print(f"  Errors                    : {len(report.errors)}")
    if report.errors:
        print("\nErrors:")
        for number, msg in report.errors:
            print(f"  - {number}: {msg}")
    if dry_run and report.created:
        print(f"\nRun with --commit to actually import {len(report.created)} invoice(s).")


if __name__ == "__main__":
    main()
