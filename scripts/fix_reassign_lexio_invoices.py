#!/usr/bin/env python3
"""Temporary one-shot script: reassign supplier invoices from Théo DAUPHY to Lexio SAS.

These invoices were incorrectly linked to contact id=47 (Théo DAUPHY) but
belong to contact id=51 (Lexio SAS).

Usage (from repo root):
    python scripts/fix_reassign_lexio_invoices.py [--commit]

Default: dry-run.  Pass --commit to apply.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "solde.db"

FROM_CONTACT_ID = 47  # Théo DAUPHY
TO_CONTACT_ID = 51    # Lexio SAS

INVOICE_NUMBERS = [
    "FF-2026040717.56.01",
    "FF-2026030215.17.01",
    "FF-2026020712.05.02",
    "FF-2026010218.42.01",
    "FF-2025113019.02.03",
    "FF-2025110211.09.00",
    "FF-2025100212.09.02",
    "FF-2025090613.37.02",
    "FF-2025090613.37.03",
    "FF-2025031313.06.00",
    "FF-2024123113.28.00",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Reassign Lexio invoices from Théo DAUPHY.")
    parser.add_argument("--commit", action="store_true", help="Apply changes (default: dry-run)")
    args = parser.parse_args()

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    # Verify source and target contacts exist
    src = con.execute("SELECT id, nom, prenom FROM contacts WHERE id = ?", (FROM_CONTACT_ID,)).fetchone()
    dst = con.execute("SELECT id, nom, prenom FROM contacts WHERE id = ?", (TO_CONTACT_ID,)).fetchone()
    if not src or not dst:
        print("ERROR: source or target contact not found in DB.")
        raise SystemExit(1)
    print(f"Source : id={src['id']}  {src['prenom']} {src['nom']}")
    print(f"Cible  : id={dst['id']}  {dst['prenom'] or ''} {dst['nom']}")
    print(f"Mode   : {'COMMIT' if args.commit else 'DRY-RUN'}")
    print()

    updated = 0
    not_found = 0
    wrong_contact = 0

    for number in INVOICE_NUMBERS:
        row = con.execute(
            "SELECT id, number, contact_id FROM invoices WHERE number = ? AND type = 'fournisseur'",
            (number,),
        ).fetchone()

        if row is None:
            print(f"  [NOT FOUND]  {number}")
            not_found += 1
            continue

        if row["contact_id"] != FROM_CONTACT_ID:
            print(f"  [SKIP]       {number}  contact_id={row['contact_id']} (déjà corrigée ou inconnue)")
            wrong_contact += 1
            continue

        if args.commit:
            con.execute(
                "UPDATE invoices SET contact_id = ? WHERE id = ?",
                (TO_CONTACT_ID, row["id"]),
            )
            con.commit()
            print(f"  [UPDATED]    {number}  id={row['id']}  {FROM_CONTACT_ID} → {TO_CONTACT_ID}")
        else:
            print(f"  [DRY-RUN]    {number}  id={row['id']}  {FROM_CONTACT_ID} → {TO_CONTACT_ID}")

        updated += 1

    con.close()

    print()
    print("=" * 55)
    print(f"  Traitées (ou à traiter) : {updated}")
    print(f"  Non trouvées en base    : {not_found}")
    print(f"  Contact différent/skip  : {wrong_contact}")
    if not args.commit:
        print()
        print("  *** Mode dry-run — relancer avec --commit pour appliquer ***")
    print("=" * 55)


if __name__ == "__main__":
    main()
