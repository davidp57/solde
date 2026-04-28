"""Settings API router — GET/PUT /api/settings (admin only)."""

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, NoReturn

import anyio
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings as get_app_config
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.settings import (
    AppSettingsRead,
    AppSettingsUpdate,
    AuditLogRead,
    BackupCreate,
    BackupFileRead,
    LogEntryRead,
    SelectiveResetPreviewRead,
    SelectiveResetRequest,
    SystemInfoRead,
    TreasurySystemOpeningRead,
    TreasurySystemOpeningUpdate,
)
from backend.services import settings as settings_service
from backend.services.audit_service import AuditAction, record_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

_AdminRequired = Annotated[User, Depends(require_role(UserRole.ADMIN))]
_AnyUserRequired = Annotated[User, Depends(get_current_user)]


def _raise_selective_reset_error(exc: Exception) -> NoReturn:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    logger.exception("Unexpected error in selective reset")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred during selective reset.",
    ) from exc


@router.get("/", response_model=AppSettingsRead)
async def get_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AnyUserRequired,
) -> AppSettingsRead:
    """Return current application settings (any authenticated user)."""
    return await settings_service.get_settings(db)  # type: ignore[return-value]


@router.put("/", response_model=AppSettingsRead)
async def update_settings(
    payload: AppSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AdminRequired,
) -> AppSettingsRead:
    """Update application settings (admin only)."""
    return await settings_service.update_settings(db, payload)  # type: ignore[return-value]


@router.get("/system-opening", response_model=TreasurySystemOpeningRead)
async def get_system_opening(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AnyUserRequired,
) -> TreasurySystemOpeningRead:
    """Return the current treasury system opening configuration (any authenticated user)."""
    return await settings_service.get_treasury_system_opening(db)


@router.put("/system-opening", response_model=TreasurySystemOpeningRead)
async def update_system_opening(
    payload: TreasurySystemOpeningUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AdminRequired,
) -> TreasurySystemOpeningRead:
    """Create or update the treasury system opening entries (admin only)."""
    return await settings_service.upsert_treasury_system_opening(db, payload)


@router.post("/reset-db", response_model=dict[str, int])
async def reset_db(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _AdminRequired,
) -> dict[str, int]:
    """Delete all application data except users. Admin only.

    Intended for demos and user-acceptance testing.
    Disabled in production (debug=False).
    """
    if not get_app_config().debug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Database reset is only available in debug mode",
        )
    result = await settings_service.reset_data(db)
    await record_audit(db, action=AuditAction.DB_RESET, actor=current_user, detail=result)
    return result


@router.post("/selective-reset/preview", response_model=SelectiveResetPreviewRead)
async def preview_selective_reset(
    payload: SelectiveResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AdminRequired,
) -> SelectiveResetPreviewRead:
    """Preview the objects that would be deleted by a selective import reset."""
    try:
        return await settings_service.preview_selective_reset(db, payload)
    except Exception as exc:  # pragma: no cover - delegated mapping below
        _raise_selective_reset_error(exc)


@router.post("/selective-reset/apply", response_model=SelectiveResetPreviewRead)
async def apply_selective_reset(
    payload: SelectiveResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _AdminRequired,
) -> SelectiveResetPreviewRead:
    """Apply a selective import reset for one import type and one fiscal year."""
    try:
        result = await settings_service.apply_selective_reset(db, payload)
    except Exception as exc:  # pragma: no cover - delegated mapping below
        _raise_selective_reset_error(exc)
    await record_audit(
        db,
        action=AuditAction.SELECTIVE_RESET,
        actor=current_user,
        detail={"import_type": payload.import_type, "fiscal_year_id": payload.fiscal_year_id},
    )
    return result


@router.post("/bootstrap-accounting", response_model=dict[str, int])
async def bootstrap_accounting(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AdminRequired,
) -> dict[str, int]:
    """Recreate the default accounting setup used during replay/testing."""
    return await settings_service.bootstrap_accounting_setup(db)


# ---------------------------------------------------------------------------
# Database backup (BL-069)
# ---------------------------------------------------------------------------

_BACKUP_DIR = "data/backups"
_MAX_BACKUPS = 5

# Regex to validate backup filenames and prevent path traversal.
# Matches: solde_backup_YYYYMMDD_HHMMSS[_label].db  (label is alphanumeric + _-)
_SAFE_BACKUP_RE = re.compile(r"^solde_backup_\d{8}_\d{6}[a-zA-Z0-9_-]*\.db$")


def _get_db_path() -> str:
    """Resolve the SQLite file path from the database URL."""
    from sqlalchemy.engine import make_url

    url = make_url(get_app_config().database_url)
    if url.get_backend_name() != "sqlite":
        raise RuntimeError(f"Backup only supports SQLite, got: {url.get_backend_name()}")
    # make_url().database returns the filesystem path for SQLite URLs
    if not url.database:
        raise RuntimeError("Cannot determine database file path from URL.")
    return url.database


def _get_backup_dir() -> str:
    """Return the backup directory path."""
    return _BACKUP_DIR


@router.post("/backup")
async def create_backup(
    _current_user: _AdminRequired,
    payload: BackupCreate | None = None,
) -> FileResponse:
    """Create a SQLite backup and return it as a downloadable file (admin only)."""
    from backend.services.backup_service import create_backup as do_backup

    db_path = _get_db_path()
    backup_dir = _get_backup_dir()

    if not Path(db_path).exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database file not found on disk.",
        )

    backup_file = await do_backup(
        db_path=db_path,
        backup_dir=backup_dir,
        max_backups=_MAX_BACKUPS,
        label=payload.label if payload else None,
    )

    return FileResponse(
        path=str(backup_file),
        filename=backup_file.name,
        media_type="application/octet-stream",
    )


# ---------------------------------------------------------------------------
# System info (BIZ-108)
# ---------------------------------------------------------------------------

_SERVER_START_TIME: datetime = datetime.now(UTC)

_LOG_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r" \[(?P<level>[A-Z]+)\]"
    r" (?P<logger>[^:]+):"
    r" (?P<message>.*)$"
)


@router.get("/system-info", response_model=SystemInfoRead)
async def get_system_info(
    _current_user: _AdminRequired,
) -> SystemInfoRead:
    """Return system information: version, DB size, uptime (admin only)."""
    cfg = get_app_config()
    from sqlalchemy.engine import make_url

    url = make_url(cfg.database_url)
    db_path = Path(url.database or "data/solde.db")
    db_size = db_path.stat().st_size if db_path.exists() else 0

    log_dir = Path("data/logs")
    log_file = str(log_dir / "solde.log")

    return SystemInfoRead(
        app_version=cfg.app_version,
        db_size_bytes=db_size,
        started_at=_SERVER_START_TIME,
        log_file=log_file,
    )


def _extract_backup_label(filename: str) -> str | None:
    """Extract the user label slug from a backup filename, if present.

    Filename format: solde_backup_YYYYMMDD_HHMMSS[_label].db
    Returns the raw slug, or None when absent.
    """
    m = re.match(r"^solde_backup_\d{8}_\d{6}_(.+)\.db$", filename)
    return m.group(1) if m else None


@router.get("/backups", response_model=list[BackupFileRead])
async def list_backups(
    _current_user: _AdminRequired,
) -> list[BackupFileRead]:
    """List existing backup files with name, size and creation date (admin only)."""
    backup_dir = Path(_BACKUP_DIR)
    if not backup_dir.exists():
        return []

    result: list[BackupFileRead] = []
    for f in sorted(backup_dir.glob("solde_backup_*.db"), reverse=True):
        stat = f.stat()
        result.append(
            BackupFileRead(
                filename=f.name,
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                label=_extract_backup_label(f.name),
            )
        )
    return result


@router.post("/backups/{filename}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup(
    filename: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _AdminRequired,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Restore a backup file and restart the application (admin only).

    The backup is copied over the live database, WAL/SHM files are removed,
    then SIGTERM is sent to the process for a clean restart.
    """
    if not _SAFE_BACKUP_RE.fullmatch(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup filename.",
        )

    backup_file = Path(_BACKUP_DIR) / filename
    if not backup_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found.",
        )

    db_path = _get_db_path()

    await record_audit(
        db,
        action=AuditAction.BACKUP_RESTORED,
        actor=current_user,
        detail={"filename": filename},
    )
    # Commit the audit entry now — the engine will be disposed in the background task.
    await db.commit()

    from backend.services.backup_service import restore_backup as do_restore  # noqa: PLC0415

    background_tasks.add_task(
        do_restore,
        filename=filename,
        backup_dir=_BACKUP_DIR,
        db_path=db_path,
    )

    return {"status": "restoring"}


@router.get("/logs", response_model=list[LogEntryRead])
async def get_logs(
    _current_user: _AdminRequired,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    levels: Annotated[list[str] | None, Query()] = None,
) -> list[LogEntryRead]:
    """Return the most recent log entries parsed from rotating log files (admin only).

    Reads files in a thread to avoid blocking the async event loop.
    Returns at most *limit* entries (default 500), most recent last.
    If *levels* is provided, only entries matching one of those levels are returned.
    """
    log_dir = Path("data/logs")
    # Current file first, then rotations in order: .1 (newest) → .2 (older) → …
    candidates = [log_dir / "solde.log"] + sorted(log_dir.glob("solde.log.*"))
    level_set = {lv.upper() for lv in levels} if levels else None

    def _read_tail() -> list[LogEntryRead]:
        collected: list[LogEntryRead] = []
        for log_file in candidates:
            if not log_file.exists():
                continue
            try:
                text = log_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            file_entries: list[LogEntryRead] = []
            current_entry: LogEntryRead | None = None
            for line in text.splitlines():
                if m := _LOG_LINE_RE.match(line):
                    if current_entry is not None:
                        file_entries.append(current_entry)
                    lvl = m.group("level")
                    if level_set and lvl not in level_set:
                        current_entry = None
                        continue
                    current_entry = LogEntryRead(
                        timestamp=m.group("ts"),
                        level=lvl,
                        logger=m.group("logger").strip(),
                        message=m.group("message"),
                    )
                elif current_entry is not None:
                    # Continuation line (e.g. stack trace frame): append to current message
                    current_entry.message = f"{current_entry.message}\n{line}"
            if current_entry is not None:
                file_entries.append(current_entry)
            # Prepend: older file lines go before current file lines
            collected = file_entries + collected
            if len(collected) >= limit:
                break
        return collected[-limit:]

    return await anyio.to_thread.run_sync(_read_tail)


# ---------------------------------------------------------------------------
# Audit log (BIZ-109)
# ---------------------------------------------------------------------------


@router.get("/audit-logs", response_model=list[AuditLogRead])
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AdminRequired,
) -> list[AuditLogRead]:
    """Return all audit log entries, most recent first (admin only)."""
    from sqlalchemy import select

    from backend.models.audit_log import AuditLog

    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1000))
    return result.scalars().all()  # type: ignore[return-value]
