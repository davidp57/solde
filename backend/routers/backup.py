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

# Shared state for OneDrive Device Authorization Flow (one-at-a-time)
_onedrive_oauth_token: str | None = None
_onedrive_oauth_proc = None  # kept for backwards compat, unused

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
    from backend.services.backup_scheduler import get_backup_progress, is_backup_running

    running = is_backup_running()
    progress = get_backup_progress() if running else 0
    if s is None:
        return BackupRunStatus(
            last_run_at=None, last_run_status=None, is_running=running, backup_progress=progress
        )
    return BackupRunStatus(
        last_run_at=s.backup_last_run_at,
        last_run_status=s.backup_last_run_status,
        last_run_error=s.backup_last_run_error,
        is_running=running,
        backup_progress=progress,
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
# OneDrive OAuth — Device Authorization Flow (RFC 8628)
#
# Works in Docker/NAS/headless environments: the user visits
# https://microsoft.com/devicelogin on any device and enters a short code.
# The server polls Microsoft until the token arrives — no redirect URI needed.
# ---------------------------------------------------------------------------

# Microsoft Graph PowerShell public client — supports device code flow.
# rclone's own client_id (b15665d9-...) is a web app, NOT eligible for device flow
# (AADSTS70002). This well-known Microsoft public client works as a drop-in.
# Override via ONEDRIVE_CLIENT_ID env var if a dedicated Azure AD app is registered.
_ONEDRIVE_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
_ONEDRIVE_DEVICE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"
_ONEDRIVE_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
_ONEDRIVE_SCOPES = "Files.Read Files.ReadWrite offline_access"


@router.get("/oauth/onedrive/start", response_model=OneDriveOAuthStart)
async def onedrive_oauth_start(
    _current_user: _AdminRequired,
) -> OneDriveOAuthStart:
    """Start the OneDrive Device Authorization Flow.

    Returns a short user_code and verification_uri for the user to visit on any
    device.  A background task polls Microsoft until the token is issued.
    """
    import httpx

    global _onedrive_oauth_token, _onedrive_oauth_proc

    _onedrive_oauth_token = None
    _onedrive_oauth_proc = None  # not used with device flow

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                _ONEDRIVE_DEVICE_URL,
                data={
                    "client_id": _ONEDRIVE_CLIENT_ID,
                    "scope": _ONEDRIVE_SCOPES,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise api_error(
            status.HTTP_502_BAD_GATEWAY,
            "ONEDRIVE_DEVICE_CODE_FAILED",
            f"Impossible de démarrer l'autorisation OneDrive : {exc}",
        ) from exc

    device_code = data["device_code"]
    interval = int(data.get("interval", 5))

    asyncio.create_task(_poll_device_token(device_code, interval))

    return OneDriveOAuthStart(
        user_code=data["user_code"],
        verification_uri=data["verification_uri"],
        expires_in=int(data.get("expires_in", 900)),
        message=data.get("message", ""),
    )


@router.get("/oauth/onedrive/status", response_model=OneDriveOAuthStatus)
async def onedrive_oauth_status(
    _current_user: _AdminRequired,
) -> OneDriveOAuthStatus:
    """Poll for the OneDrive token (consumed once available)."""
    global _onedrive_oauth_token

    if _onedrive_oauth_token is not None:
        token = _onedrive_oauth_token
        _onedrive_oauth_token = None
        return OneDriveOAuthStatus(done=True, token=token)
    return OneDriveOAuthStatus(done=False)


async def _poll_device_token(device_code: str, interval: int) -> None:
    """Background task: poll Microsoft token endpoint until granted or expired."""
    import json as _json
    from datetime import UTC, datetime, timedelta

    import httpx

    global _onedrive_oauth_token

    max_wait = 900  # 15 min
    waited = 0

    while waited < max_wait:
        await asyncio.sleep(interval)
        waited += interval
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    _ONEDRIVE_TOKEN_URL,
                    data={
                        "grant_type": ("urn:ietf:params:oauth:grant-type:device_code"),
                        "client_id": _ONEDRIVE_CLIENT_ID,
                        "device_code": device_code,
                    },
                )
                data = resp.json()

            error = data.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval = min(interval + 5, 30)
                continue
            if error in ("expired_token", "access_denied", "bad_verification_code"):
                logger.warning("OneDrive device flow ended: %s", error)
                return

            if "access_token" not in data:
                logger.warning("Unexpected device flow response: %s", data)
                return

            # Build rclone-compatible token JSON
            expiry = datetime.now(UTC) + timedelta(seconds=int(data.get("expires_in", 3600)))
            rclone_token = _json.dumps(
                {
                    "access_token": data["access_token"],
                    "token_type": data.get("token_type", "Bearer"),
                    "refresh_token": data.get("refresh_token", ""),
                    "expiry": expiry.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
                }
            )

            # Fetch drive_id from Microsoft Graph
            drive_id = ""
            drive_type = "personal"
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    gr = await client.get(
                        "https://graph.microsoft.com/v1.0/me/drive",
                        headers={"Authorization": f"Bearer {data['access_token']}"},
                    )
                    if gr.is_success:
                        gdata = gr.json()
                        drive_id = gdata.get("id", "")
                        drive_type = gdata.get("driveType", "personal")
            except Exception as exc:
                logger.warning("Could not fetch OneDrive drive_id: %s", exc)

            # Package as rclone_config JSON.
            # client_id MUST be included so rclone uses it for token refresh;
            # without it rclone falls back to its built-in web-app client_id which
            # would reject a refresh_token issued for a different client.
            _onedrive_oauth_token = _json.dumps(
                {
                    "token": rclone_token,
                    "drive_id": drive_id,
                    "drive_type": drive_type,
                    "client_id": _ONEDRIVE_CLIENT_ID,
                    "client_secret": "",  # public client — no secret
                }
            )
            logger.info("OneDrive device flow: token obtained (drive_id=%s)", drive_id)
            return

        except Exception as exc:
            logger.warning("OneDrive device flow poll error: %s", exc)

    logger.warning("OneDrive device flow: timed out after %d s", max_wait)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _regenerate_rclone_conf(db: AsyncSession) -> None:
    """Reload all destinations from DB and rewrite rclone.conf."""
    from backend.services.backup_destination_service import write_rclone_config

    result = await db.execute(select(BackupDestination).order_by(BackupDestination.id))
    dests = list(result.scalars().all())
    write_rclone_config(dests)
