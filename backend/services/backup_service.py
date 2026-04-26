"""SQLite online backup with rotation (BL-069) and restore (BIZ-116)."""

import os
import re
import shutil
import signal
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import anyio


def _slugify_label(label: str) -> str:
    """Convert a label to a safe filename slug (max 50 chars)."""
    # Keep only allowed chars
    slug = re.sub(r"[^a-zA-Z0-9 _-]", "", label).strip()
    # Collapse spaces to underscores
    slug = re.sub(r"\s+", "_", slug)
    # Collapse consecutive separators
    slug = re.sub(r"[_-]{2,}", "_", slug)
    return slug[:50]


async def create_backup(
    *,
    db_path: str,
    backup_dir: str,
    max_backups: int = 5,
    label: str | None = None,
) -> Path:
    """Create a backup of the SQLite database using ``sqlite3.backup()``.

    If *label* is provided it is slugified and appended to the filename.
    Returns the path to the new backup file.  Older backups beyond
    *max_backups* are deleted automatically (FIFO).
    """
    if max_backups < 1:
        raise ValueError("max_backups must be >= 1")

    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    name = f"solde_backup_{timestamp}"
    if label and (slug := _slugify_label(label)):
        name = f"{name}_{slug}"
    dest_file = backup_path / f"{name}.db"

    # Run blocking sqlite3 I/O in a worker thread to avoid blocking the event loop.
    await anyio.to_thread.run_sync(lambda: _do_backup(db_path, dest_file))

    _rotate_backups(backup_path, max_backups)

    return dest_file


def _do_backup(db_path: str, dest_file: Path) -> None:
    """Perform the actual sqlite3.backup() (synchronous, called from a thread)."""
    src_conn = sqlite3.connect(db_path)
    dst_conn = sqlite3.connect(str(dest_file))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()


def _rotate_backups(backup_dir: Path, max_backups: int) -> None:
    """Keep only the *max_backups* most recent ``.db`` files."""
    backups = sorted(backup_dir.glob("solde_backup_*.db"))
    while len(backups) > max_backups:
        oldest = backups.pop(0)
        oldest.unlink(missing_ok=True)


async def restore_backup(
    *,
    filename: str,
    backup_dir: str,
    db_path: str,
) -> None:
    """Restore a backup file and restart the process.

    Sequence:
    1. Dispose the SQLAlchemy engine (closes all pooled connections).
    2. Copy the backup file over the live database (in a worker thread).
    3. Delete WAL and SHM side-files to avoid inconsistency.
    4. Send SIGTERM to self to trigger a clean restart.
    """
    from backend.database import _engine  # noqa: PLC0415

    # Dispose engine so SQLAlchemy connections are closed before the file copy.
    await _engine.dispose()

    backup_file = Path(backup_dir) / filename
    db = Path(db_path)

    await anyio.to_thread.run_sync(lambda: _do_restore(backup_file, db))

    os.kill(os.getpid(), signal.SIGTERM)


def _do_restore(backup_file: Path, db_path: Path) -> None:
    """Copy backup over live DB and remove WAL/SHM files (synchronous)."""
    wal = Path(f"{db_path}-wal")
    shm = Path(f"{db_path}-shm")
    for side_file in (wal, shm):
        side_file.unlink(missing_ok=True)
    shutil.copy2(str(backup_file), str(db_path))
