"""Service for backup restore operations.

Provides:
- test_restore: integrity check on a backup file (dry-run, no side effects)
- restore_from_destination: fetch remote backup then call restore_backup()
"""

import logging
import sqlite3
from pathlib import Path

import anyio

from backend.schemas.backup import BackupRestoreTestResult

logger = logging.getLogger(__name__)

# Tables that must exist in a valid Solde database backup.
_EXPECTED_TABLES = frozenset(
    {
        "users",
        "app_settings",
        "contacts",
        "accounting_accounts",
        "accounting_entries",
        "accounting_rules",
        "invoices",
        "invoice_lines",
        "payments",
        "bank_transactions",
        "deposits",
        "cash_register",
        "fiscal_years",
        "salaries",
        "import_logs",
    }
)


def _do_test_restore(backup_path: Path) -> BackupRestoreTestResult:
    """Synchronous integrity check on a backup file (called from a thread)."""
    try:
        conn = sqlite3.connect(str(backup_path))
    except Exception as exc:
        return BackupRestoreTestResult(
            ok=False,
            integrity_check="",
            error=f"Impossible d'ouvrir le fichier : {exc}",
        )

    try:
        # Integrity check
        cursor = conn.execute("PRAGMA integrity_check")
        rows = cursor.fetchall()
        integrity = rows[0][0] if rows else "no result"

        # Table presence check
        cursor2 = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        found_tables = {row[0] for row in cursor2.fetchall()}

        tables_found = sorted(found_tables & _EXPECTED_TABLES)
        tables_missing = sorted(_EXPECTED_TABLES - found_tables)

        ok = integrity == "ok" and not tables_missing
        return BackupRestoreTestResult(
            ok=ok,
            integrity_check=integrity,
            tables_found=tables_found,
            tables_missing=tables_missing,
        )
    except Exception as exc:
        return BackupRestoreTestResult(
            ok=False,
            integrity_check="",
            error=f"Erreur lors de la vérification : {exc}",
        )
    finally:
        conn.close()


async def test_restore(backup_path: str) -> BackupRestoreTestResult:
    """Async wrapper: run integrity check in a worker thread."""
    path = Path(backup_path)
    if not path.exists():
        return BackupRestoreTestResult(
            ok=False,
            integrity_check="",
            error="Fichier introuvable",
        )
    return await anyio.to_thread.run_sync(lambda: _do_test_restore(path))


async def restore_from_destination(
    dest: object,
    filename: str,
    backup_dir: str,
    db_path: str,
) -> None:
    """Fetch a backup from a remote destination then restore it.

    For local destinations the file must already be present in backup_dir.
    For remote destinations it is copied locally first via rclone.
    """
    from backend.models.backup_destination import BackupDestination
    from backend.services.backup_destination_service import fetch_remote_backup
    from backend.services.backup_service import restore_backup

    if isinstance(dest, BackupDestination) and dest.type != "local":
        # Fetch remote file locally first
        local_path = Path(backup_dir) / filename
        if not local_path.exists():
            await fetch_remote_backup(dest, filename, backup_dir)

    await restore_backup(filename=filename, backup_dir=backup_dir, db_path=db_path)
