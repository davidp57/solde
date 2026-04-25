"""Settings API router — GET/PUT /api/settings (admin only)."""

import logging
from pathlib import Path
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings as get_app_config
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.settings import (
    AppSettingsRead,
    AppSettingsUpdate,
    SelectiveResetPreviewRead,
    SelectiveResetRequest,
    TreasurySystemOpeningRead,
    TreasurySystemOpeningUpdate,
)
from backend.services import settings as settings_service
from backend.services.audit_service import AuditAction, record_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

_AdminRequired = Annotated[User, Depends(require_role(UserRole.ADMIN))]


def _raise_selective_reset_error(exc: Exception) -> NoReturn:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    logger.exception("Unexpected error in selective reset")
    raise exc


@router.get("/", response_model=AppSettingsRead)
async def get_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AdminRequired,
) -> AppSettingsRead:
    """Return current application settings (admin only)."""
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
    _current_user: _AdminRequired,
) -> TreasurySystemOpeningRead:
    """Return the current treasury system opening configuration (admin only)."""
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
    )

    return FileResponse(
        path=str(backup_file),
        filename=backup_file.name,
        media_type="application/octet-stream",
    )
