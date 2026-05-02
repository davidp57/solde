#!/usr/bin/env python3
"""One-shot script: bulk-attach existing supplier invoice files to their DB records.

Scans data/factures_fournisseur/ recursively, matches each file by its stem
(= invoice number) against the invoices table, and copies matched files to
data/uploads/invoices/ while updating invoice.file_path.

Usage (from repo root):
    python scripts/attach_supplier_invoices.py [--db data/solde.db] [--commit]

Default mode is dry-run (no DB writes, no file copies).  Pass --commit to apply.

Rules:
  - Files are processed in descending order by filename (most recent first).
  - The 2 most recent files are skipped (already attached).
  - .docx files are skipped with a warning (unsupported type).
  - If an invoice is not found in the DB: warning only, no error.
  - If invoice.file_path is already set: skipped silently.
  - Supported extensions: .pdf, .jpg, .jpeg, .png, .webp
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "data" / "factures_fournisseur"
UPLOAD_DIR = REPO_ROOT / "data" / "uploads" / "invoices"
DEFAULT_DB = REPO_ROOT / "data" / "solde.db"

# Number of most-recent files (by sorted name desc) to skip -- already attached.
SKIP_MOST_RECENT = 2

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
UNSUPPORTED_EXTENSIONS = {".docx", ".doc", ".odt"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def collect_files(source_dir: Path) -> list[Path]:
    """Return all files under source_dir recursively, sorted descending by stem."""
    files = [
        p
        for p in source_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS | UNSUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=lambda p: p.stem, reverse=True)


def attach(db_path: Path, files: list[Path], commit: bool) -> None:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    stats = {"attached": 0, "skipped_already": 0, "skipped_unsupported": 0, "not_found": 0}

    for path in files:
        stem = path.stem
        ext = path.suffix.lower()

        if ext in UNSUPPORTED_EXTENSIONS:
            print(f"  [SKIP-TYPE]  {path.relative_to(REPO_ROOT)}  -- extension {ext!r} non supportee")
            stats["skipped_unsupported"] += 1
            continue

        row = con.execute(
            "SELECT id, file_path FROM invoices WHERE number = ? AND type = 'fournisseur'",
            (stem,),
        ).fetchone()

        if row is None:
            print(f"  [NOT FOUND]  {stem}  -- aucune facture fournisseur trouvee en base")
            stats["not_found"] += 1
            continue

        invoice_id: int = row["id"]
        existing_path: str | None = row["file_path"]

        if existing_path:
            stats["skipped_already"] += 1
            continue  # already attached, silent skip

        safe_name = f"{uuid.uuid4().hex}{ext}"
        dest = UPLOAD_DIR / safe_name

        if commit:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            # Store the path as seen from inside the Docker container (/app is the workdir).
            docker_path = f"/app/data/uploads/invoices/{safe_name}"
            con.execute(
                "UPDATE invoices SET file_path = ? WHERE id = ?",
                (docker_path, invoice_id),
            )
            con.commit()
            print(f"  [ATTACHED]   {stem}  ->  {dest.relative_to(REPO_ROOT)}")
        else:
            print(f"  [DRY-RUN]    {stem}  ->  {safe_name}  (id={invoice_id})")

        stats["attached"] += 1

    con.close()

    print()
    print("=" * 60)
    print(f"  Attachees       : {stats['attached']}")
    print(f"  Deja liees      : {stats['skipped_already']}")
    print(f"  Non trouvees DB : {stats['not_found']}")
    print(f"  Type ignore     : {stats['skipped_unsupported']}")
    if not commit:
        print()
        print("  *** Mode dry-run -- relancer avec --commit pour appliquer ***")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk-attach supplier invoice files.")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help="Path to solde.db (default: data/solde.db)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually copy files and update the database (default: dry-run)",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.is_file():
        print(f"ERROR: database not found: {db_path}", flush=True)
        raise SystemExit(1)

    if not SOURCE_DIR.is_dir():
        print(f"ERROR: source directory not found: {SOURCE_DIR}", flush=True)
        raise SystemExit(1)

    all_files = collect_files(SOURCE_DIR)
    print(f"Fichiers trouves : {len(all_files)}  (skip des {SKIP_MOST_RECENT} plus recents)")
    files_to_process = all_files[SKIP_MOST_RECENT:]
    print(f"Fichiers a traiter : {len(files_to_process)}")
    print(f"Mode : {'COMMIT' if args.commit else 'DRY-RUN'}")
    print()

    attach(db_path, files_to_process, commit=args.commit)


if __name__ == "__main__":
    main()
