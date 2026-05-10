"""Backup router — admin endpoints for backup destinations, scheduling and restore."""

import asyncio
import logging
import re
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import api_error
from backend.models.backup_destination import BackupDestination
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.backup import (
    BackupConnectionTestResult,
    BackupDestinationCreate,
    BackupDestinationRead,
    BackupDestinationUpdate,
    BackupRestoreTestResult,
    BackupRunStatus,
    BackupScheduleRead,
    BackupScheduleUpdate,
    OneDriveOAuthStart,
    OneDriveOAuthStatus,
)
from backend.services.audit_service import AuditAction, record_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["backup"])

_AdminRequired = Annotated[User, Depends(require_role(UserRole.ADMIN))]

# Shared state for OneDrive OAuth (one-at-a-time flow)
_onedrive_oauth_token: str | None = None
_onedrive_oauth_proc: asyncio.subprocess.Process | None = None

# Regex to validate backup filenames and prevent path traversal.
_SAFE_BACKUP_RE = re.compile(r"^solde_backup_(?:\d{8}_\d{6}|\d{14})[a-zA-Z0-9_-]*\.db$")
_BACKUP_DIR = "data/backups"


def _get_db_path() -> str:
    from sqlalchemy.engine import make_url

    from backend.config import get_settings

    url = make_url(get_settings().database_url)
    if not url.database:
        raise RuntimeError("Cannot determine database file path from URL.")
    return url.database


# ---------------------------------------------------------------------------
# Destinations
# ---------------------------------------------------------------------------


@router.get("/destinations", response_model=list[BackupDestinationRead])
async def list_destinations(
    _current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[BackupDestinationRead]:
    """List all backup destinations."""
    result = await db.execute(select(BackupDestination).order_by(BackupDestination.id))
    dests = result.scalars().all()
    return [BackupDestinationRead.model_validate(d) for d in dests]


@router.post(
    "/destinations", response_model=BackupDestinationRead, status_code=status.HTTP_201_CREATED
)
async def create_destination(
    payload: BackupDestinationCreate,
    current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackupDestinationRead:
    """Create a backup destination and regenerate rclone.conf."""
    dest = BackupDestination(
        name=payload.name,
        type=payload.type,
        enabled=payload.enabled,
        rclone_remote_name=payload.rclone_remote_name,
        rclone_config=payload.rclone_config,
        target_path=payload.target_path,
    )
    db.add(dest)
    await db.flush()
    await _regenerate_rclone_conf(db)
    await record_audit(
        db,
        action=AuditAction.BACKUP_DESTINATION_CREATED,
        actor=current_user,
        detail={"action": "create_backup_destination", "name": payload.name},
    )
    await db.commit()
    await db.refresh(dest)
    return BackupDestinationRead.model_validate(dest)


@router.put("/destinations/{destination_id}", response_model=BackupDestinationRead)
async def update_destination(
    destination_id: int,
    payload: BackupDestinationUpdate,
    current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackupDestinationRead:
    """Update a backup destination."""
    result = await db.execute(
        select(BackupDestination).where(BackupDestination.id == destination_id)
    )
    dest = result.scalar_one_or_none()
    if dest is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "DEST_NOT_FOUND", "Destination introuvable.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dest, field, value)

    await _regenerate_rclone_conf(db)
    await record_audit(
        db,
        action=AuditAction.BACKUP_DESTINATION_UPDATED,
        actor=current_user,
        detail={"action": "update_backup_destination", "id": destination_id},
    )
    await db.commit()
    await db.refresh(dest)
    return BackupDestinationRead.model_validate(dest)


@router.delete("/destinations/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_destination(
    destination_id: int,
    current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a backup destination."""
    result = await db.execute(
        select(BackupDestination).where(BackupDestination.id == destination_id)
    )
    dest = result.scalar_one_or_none()
    if dest is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "DEST_NOT_FOUND", "Destination introuvable.")

    await db.delete(dest)
    await _regenerate_rclone_conf(db)
    await record_audit(
        db,
        action=AuditAction.BACKUP_DESTINATION_DELETED,
        actor=current_user,
        detail={"action": "delete_backup_destination", "id": destination_id},
    )
    await db.commit()


@router.post("/destinations/{destination_id}/test", response_model=BackupConnectionTestResult)
async def test_destination(
    destination_id: int,
    _current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackupConnectionTestResult:
    """Test connectivity for a backup destination."""
    from backend.services.backup_destination_service import test_destination_connection

    result = await db.execute(
        select(BackupDestination).where(BackupDestination.id == destination_id)
    )
    dest = result.scalar_one_or_none()
    if dest is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "DEST_NOT_FOUND", "Destination introuvable.")

    return await test_destination_connection(dest)


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------


@router.get("/schedule", response_model=BackupScheduleRead)
async def get_schedule(
    _current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackupScheduleRead:
    """Return current backup schedule settings."""
    from backend.models.app_settings import AppSettings

    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    s = result.scalar_one_or_none()
    if s is None:
        raise api_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "SETTINGS_NOT_FOUND",
            "Settings not found.",
        )
    return BackupScheduleRead.from_settings(s)


@router.put("/schedule", response_model=BackupScheduleRead)
async def update_schedule(
    payload: BackupScheduleUpdate,
    current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackupScheduleRead:
    """Update backup schedule settings and reload the scheduler."""
    from backend.models.app_settings import AppSettings
    from backend.services.backup_scheduler import reload_scheduler

    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    s = result.scalar_one_or_none()
    if s is None:
        raise api_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "SETTINGS_NOT_FOUND",
            "Settings not found.",
        )

    if payload.enabled is not None:
        s.backup_enabled = payload.enabled
    if payload.schedule_type is not None:
        s.backup_schedule_type = payload.schedule_type
    if payload.interval_hours is not None:
        s.backup_interval_hours = payload.interval_hours
    if payload.cron_expression is not None:
        s.backup_cron_expression = payload.cron_expression
    if payload.include_uploads is not None:
        s.backup_include_uploads = payload.include_uploads
    if payload.notify_on_failure is not None:
        s.backup_notify_on_failure = payload.notify_on_failure

    await record_audit(
        db,
        action=AuditAction.SETTINGS_UPDATED,
        actor=current_user,
        detail={"action": "update_backup_schedule"},
    )
    await db.commit()
    await db.refresh(s)

    reload_scheduler(s)
    return BackupScheduleRead.from_settings(s)


# ---------------------------------------------------------------------------
# Manual run + status
# ---------------------------------------------------------------------------


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def trigger_backup(
    _current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Trigger an immediate backup (runs in background)."""
    from backend.services.backup_scheduler import run_backup_job

    db_path = _get_db_path()
    backup_dir = str(Path(_BACKUP_DIR).resolve())

    from backend.models.app_settings import AppSettings

    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    s = result.scalar_one_or_none()
    include_uploads = s.backup_include_uploads if s else True
    notify_on_failure = s.backup_notify_on_failure if s else False

    background_tasks.add_task(
        run_backup_job,
        db_path=db_path,
        backup_dir=backup_dir,
        include_uploads=include_uploads,
        notify_on_failure=notify_on_failure,
    )
    return {"status": "started"}


@router.get("/status", response_model=BackupRunStatus)
async def get_status(
    _current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackupRunStatus:
    """Return status of the last backup run."""
    from backend.models.app_settings import AppSettings

    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    s = result.scalar_one_or_none()
    if s is None:
        return BackupRunStatus(last_run_at=None, last_run_status=None)
    return BackupRunStatus(
        last_run_at=s.backup_last_run_at,
        last_run_status=s.backup_last_run_status,
        last_run_error=s.backup_last_run_error,
    )


# ---------------------------------------------------------------------------
# Test-restore and restore
# ---------------------------------------------------------------------------


@router.post("/backups/{filename}/test-restore", response_model=BackupRestoreTestResult)
async def test_restore_backup(
    filename: str,
    _current_user: _AdminRequired,
) -> BackupRestoreTestResult:
    """Dry-run integrity check on a local backup file."""
    from backend.services.backup_restore_service import test_restore

    if not _SAFE_BACKUP_RE.fullmatch(filename):
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "BACKUP_INVALID_FILENAME",
            "Nom de fichier invalide.",
        )

    backup_path = str(Path(_BACKUP_DIR) / filename)
    return await test_restore(backup_path)


@router.post("/backups/{filename}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup_endpoint(
    filename: str,
    current_user: _AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    destination_id: Annotated[int | None, Query()] = None,
) -> dict[str, str]:
    """Restore a backup file (local or fetched from a remote destination)."""
    from backend.services.backup_restore_service import restore_from_destination

    if not _SAFE_BACKUP_RE.fullmatch(filename):
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "BACKUP_INVALID_FILENAME",
            "Nom de fichier invalide.",
        )

    dest = None
    if destination_id is not None:
        result = await db.execute(
            select(BackupDestination).where(BackupDestination.id == destination_id)
        )
        dest = result.scalar_one_or_none()
        if dest is None:
            raise api_error(status.HTTP_404_NOT_FOUND, "DEST_NOT_FOUND", "Destination introuvable.")

    db_path = _get_db_path()
    await record_audit(
        db,
        action=AuditAction.BACKUP_RESTORED,
        actor=current_user,
        detail={"filename": filename, "destination_id": destination_id},
    )
    await db.commit()

    background_tasks.add_task(
        restore_from_destination,
        dest=dest,
        filename=filename,
        backup_dir=_BACKUP_DIR,
        db_path=db_path,
    )
    return {"status": "restoring"}


# ---------------------------------------------------------------------------
# OneDrive OAuth
# ---------------------------------------------------------------------------


@router.get("/oauth/onedrive/start", response_model=OneDriveOAuthStart)
async def onedrive_oauth_start(
    _current_user: _AdminRequired,
) -> OneDriveOAuthStart:
    """Start the OneDrive OAuth2 flow via rclone authorize.

    Returns the port and auth URL for the user to open in their browser.
    """
    global _onedrive_oauth_proc, _onedrive_oauth_token

    _onedrive_oauth_token = None

    # rclone's public client_id only has http://127.0.0.1:53682/ registered as redirect_uri.
    # We must use that exact port, and bind on 0.0.0.0 so the callback is reachable from the
    # browser (Docker maps host:53682 → container:53682 via docker-compose).
    port = 53682

    cmd = [
        "rclone",
        "authorize",
        "onedrive",
        "--auth-no-open-browser",
        f"--auth-addr=0.0.0.0:{port}",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise api_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "RCLONE_NOT_FOUND",
            "rclone n'est pas installé ou introuvable dans le PATH.",
        ) from exc

    _onedrive_oauth_proc = proc

    # Schedule background token capture
    asyncio.create_task(_capture_onedrive_token(proc))

    auth_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        f"?client_id=b15665d9-eda6-4092-8539-0eec376afd59"
        f"&response_type=code"
        f"&redirect_uri=http%3A%2F%2F127.0.0.1%3A{port}%2F"
        f"&scope=Files.Read+Files.ReadWrite+offline_access"
    )

    return OneDriveOAuthStart(port=port, auth_url=auth_url)


@router.get("/oauth/onedrive/status", response_model=OneDriveOAuthStatus)
async def onedrive_oauth_status(
    _current_user: _AdminRequired,
) -> OneDriveOAuthStatus:
    """Poll for the OneDrive OAuth2 token captured by rclone."""
    global _onedrive_oauth_token

    if _onedrive_oauth_token is not None:
        token = _onedrive_oauth_token
        _onedrive_oauth_token = None
        return OneDriveOAuthStatus(done=True, token=token)
    return OneDriveOAuthStatus(done=False)


async def _capture_onedrive_token(proc: asyncio.subprocess.Process) -> None:
    """Background task: capture the token from rclone authorize output."""
    global _onedrive_oauth_token

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        # rclone authorize may print the token JSON to stdout or stderr
        output = ""
        if stdout:
            output += stdout.decode(errors="replace")
        if stderr:
            output += stderr.decode(errors="replace")
        import json as _json

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("{") and "access_token" in line:
                try:
                    _json.loads(line)  # validate JSON
                    _onedrive_oauth_token = line
                    return
                except ValueError:
                    pass
    except (TimeoutError, Exception) as exc:
        logger.warning("OneDrive OAuth token capture failed: %s", exc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _regenerate_rclone_conf(db: AsyncSession) -> None:
    """Reload all destinations from DB and rewrite rclone.conf."""
    from backend.services.backup_destination_service import write_rclone_config

    result = await db.execute(select(BackupDestination).order_by(BackupDestination.id))
    dests = list(result.scalars().all())
    write_rclone_config(dests)
