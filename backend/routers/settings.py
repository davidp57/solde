"""Settings API router — GET/PUT /api/settings (admin only)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.settings import AppSettingsRead, AppSettingsUpdate
from backend.services import settings as settings_service

router = APIRouter(prefix="/settings", tags=["settings"])

_AdminRequired = Annotated[User, Depends(require_role(UserRole.ADMIN))]


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


@router.post("/reset-db", response_model=dict[str, int])
async def reset_db(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _AdminRequired,
) -> dict[str, int]:
    """Delete all transactional data (contacts, invoices, payments, bank, cash, entries,
    salaries) while preserving users, settings, chart of accounts and accounting rules.
    Admin only. Intended for demos and user-acceptance testing.
    """
    return await settings_service.reset_data(db)
