"""Settings API router — GET/PUT /api/settings (admin only)."""

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
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
    _current_user: _AdminRequired,
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
    return await settings_service.reset_data(db)


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
    _current_user: _AdminRequired,
) -> SelectiveResetPreviewRead:
    """Apply a selective import reset for one import type and one fiscal year."""
    try:
        return await settings_service.apply_selective_reset(db, payload)
    except Exception as exc:  # pragma: no cover - delegated mapping below
        _raise_selective_reset_error(exc)


@router.post("/bootstrap-accounting", response_model=dict[str, int])
async def bootstrap_accounting(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AdminRequired,
) -> dict[str, int]:
    """Recreate the default accounting setup used during replay/testing."""
    return await settings_service.bootstrap_accounting_setup(db)
