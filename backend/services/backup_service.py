"""SQLite online backup with rotation (BL-069)."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path


async def create_backup(
    *,
    db_path: str,
    backup_dir: str,
    max_backups: int = 5,
) -> Path:
    """Create a backup of the SQLite database using ``sqlite3.backup()``.

    Returns the path to the new backup file.  Older backups beyond
    *max_backups* are deleted automatically (FIFO).
    """
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    dest_file = backup_path / f"solde_backup_{timestamp}.db"

    # sqlite3.backup() is synchronous — safe on a single-writer SQLite WAL DB.
    src_conn = sqlite3.connect(db_path)
    dst_conn = sqlite3.connect(str(dest_file))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    _rotate_backups(backup_path, max_backups)

    return dest_file


def _rotate_backups(backup_dir: Path, max_backups: int) -> None:
    """Keep only the *max_backups* most recent ``.db`` files."""
    backups = sorted(backup_dir.glob("solde_backup_*.db"))
    while len(backups) > max_backups:
        oldest = backups.pop(0)
        oldest.unlink(missing_ok=True)
