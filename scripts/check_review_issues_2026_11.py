#!/usr/bin/env python3
"""Read-only check: did issues #164, #165, #195, #196 and #197 leave marks in a database?

Opens the SQLite file read-only and never writes. Run it on a copy of the
production database (a backup downloaded from Administration → Sauvegardes, or
the three ``solde.db*`` files copied together).

Each issue ends on a ``VERDICT`` line; the rows printed above it are what to look
at when the verdict is not "rien".

Usage (from repo root):
    python scripts/check_review_issues_2026_11.py path/to/solde.db [path/to/logs]
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)


def check_165(db: sqlite3.Connection) -> None:
    print("\n=== #165 — numéros d'écriture en double (migration 0052)")
    version = db.execute("SELECT version_num FROM alembic_version").fetchone()
    print(f"version de schéma : {version[0] if version else '?'}")
    dupes = db.execute(
        "SELECT entry_number, COUNT(*) FROM accounting_entries "
        "GROUP BY entry_number HAVING COUNT(*) > 1 ORDER BY entry_number"
    ).fetchall()
    for number, count in dupes:
        print(f"  {number} : {count} lignes")
    if dupes:
        print(f"VERDICT #165 : {len(dupes)} numéro(s) en double — la migration les renumérotera")
    else:
        print("VERDICT #165 : rien — aucun doublon, la base a déjà passé la migration 0052")


def check_164(logs_dir: Path | None) -> None:
    print("\n=== #164 — collision de numéro d'écriture à l'enregistrement")
    if logs_dir is None:
        print("VERDICT #164 : non vérifié — passer le dossier des journaux en 2e argument")
        return
    needle = "UNIQUE constraint failed: accounting_entries.entry_number"
    hits: list[str] = []
    for log in sorted(logs_dir.rglob("*.log*")):
        with log.open(encoding="utf-8", errors="replace") as handle:
            hits.extend(f"  {log.name}: {line.strip()[:160]}" for line in handle if needle in line)
    for hit in hits[:20]:
        print(hit)
    if hits:
        print(
            f"VERDICT #164 : {len(hits)} collision(s) dans les journaux — chaque ligne est un "
            "enregistrement refusé (erreur 500), rien n'a été écrit en base pour lui"
        )
    else:
        print("VERDICT #164 : rien — aucune collision dans les journaux conservés")


def check_197(db: sqlite3.Connection) -> None:
    print("\n=== #197 — clôture et report à nouveau dans le même groupe du journal")
    rows = db.execute(
        "SELECT e.source_id, closed.name, e.fiscal_year_id, opened.name, COUNT(*) "
        "FROM accounting_entries e "
        "LEFT JOIN fiscal_years closed ON closed.id = e.source_id "
        "LEFT JOIN fiscal_years opened ON opened.id = e.fiscal_year_id "
        "WHERE e.source_type = 'cloture' AND e.fiscal_year_id IS NOT NULL "
        "AND e.source_id IS NOT NULL AND e.fiscal_year_id != e.source_id "
        "GROUP BY e.source_id, e.fiscal_year_id"
    ).fetchall()
    for _, closed, _, opened, count in rows:
        print(f"  report à nouveau de {closed} vers {opened} : {count} ligne(s)")
    if rows:
        print(
            "VERDICT #197 : affichage seulement — ces lignes se mélangeaient à la clôture dans "
            "le journal groupé ; aucun montant n'est faux. La migration c3d9a1e5f702 les reclasse."
        )
    else:
        print("VERDICT #197 : rien — aucun report à nouveau généré par l'application")


def check_195(db: sqlite3.Connection) -> None:
    print("\n=== #195 — remise de chèques fusionnée dans un bordereau d'espèces (ou l'inverse)")
    # A wrong merge needs a confirmed cash slip and a confirmed cheque slip of the
    # same amount, close enough for one statement row to fall in both 10-day windows.
    pairs = db.execute(
        "SELECT esp.id, esp.date, chq.id, chq.date, esp.total_amount "
        "FROM deposits esp JOIN deposits chq "
        "ON esp.type = 'especes' AND chq.type = 'cheques' "
        "AND ROUND(CAST(esp.total_amount AS REAL), 2) = ROUND(CAST(chq.total_amount AS REAL), 2) "
        "AND ABS(julianday(esp.date) - julianday(chq.date)) <= 20 "
        "WHERE esp.confirmed = 1 AND chq.confirmed = 1 "
        "ORDER BY esp.date"
    ).fetchall()
    for esp_id, esp_date, chq_id, chq_date, amount in pairs:
        print(f"  espèces #{esp_id} du {esp_date} et chèques #{chq_id} du {chq_date} : {amount} €")
        for slip_id in (esp_id, chq_id):
            for line in db.execute(
                "SELECT id, date, source, reference, reconciled, reconciled_with, description "
                "FROM bank_transactions WHERE description LIKE ?",
                (f"%(bordereau #{slip_id})%",),
            ):
                print(f"      ligne banque {line}")
    if pairs:
        print(
            f"VERDICT #195 : {len(pairs)} paire(s) à regarder — une fusion à tort se voit à une "
            "ligne de relevé (source import) dont la description nomme le bordereau d'espèces "
            "alors que le relevé portait une remise de chèques, ou l'inverse"
        )
    else:
        print("VERDICT #195 : rien — aucune paire de bordereaux qui aurait permis l'erreur")


def check_196(db: sqlite3.Connection) -> None:
    print("\n=== #196 — règlement en espèces annulé après sa remise en banque")
    columns = {row[1] for row in db.execute("PRAGMA table_info(audit_logs)")}
    label = "target_label" if "target_label" in columns else "'règlement #' || target_id"
    cancelled = db.execute(
        f"SELECT id, created_at, {label}, json_extract(detail, '$.amount') "
        "FROM audit_logs WHERE action = 'payment.delete' "
        "AND json_extract(detail, '$.method') = 'especes' ORDER BY created_at"
    ).fetchall()
    suspects = 0
    for audit_id, cancelled_at, label, amount in cancelled:
        # The payment row is gone, so its date is unknown: a cash slip confirmed before
        # the cancellation is the necessary condition.
        slips = db.execute(
            "SELECT id, date, total_amount FROM deposits "
            "WHERE type = 'especes' AND confirmed = 1 AND confirmed_date <= date(?) "
            "ORDER BY date DESC LIMIT 3",
            (cancelled_at,),
        ).fetchall()
        flag = "À VÉRIFIER" if slips else "ok"
        suspects += bool(slips)
        print(f"  [{flag}] annulé le {cancelled_at} : {label} ({amount} €), audit #{audit_id}")
        for slip in slips:
            print(f"      remise d'espèces confirmée avant : #{slip[0]} du {slip[1]} ({slip[2]} €)")
    if suspects:
        print(
            f"VERDICT #196 : {suspects} annulation(s) à vérifier — si la remise listée est datée "
            "du jour du règlement ou après, la caisse a été débitée deux fois de ce montant"
        )
    else:
        print("VERDICT #196 : rien — aucune annulation d'espèces après une remise confirmée")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    db_path = Path(sys.argv[1])
    logs_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    db = _connect(db_path)
    try:
        check_165(db)
        check_164(logs_dir)
        check_197(db)
        check_195(db)
        check_196(db)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
