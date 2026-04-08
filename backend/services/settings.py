"""Application settings service — read and update the single settings row."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.app_settings import AppSettings
from backend.schemas.settings import AppSettingsUpdate

_SETTINGS_ID = 1


async def get_settings(db: AsyncSession) -> AppSettings:
    """Return the settings row, creating it with defaults if absent."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == _SETTINGS_ID))
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = AppSettings(id=_SETTINGS_ID)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


async def update_settings(db: AsyncSession, payload: AppSettingsUpdate) -> AppSettings:
    """Partially update settings with provided fields."""
    settings = await get_settings(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.commit()
    await db.refresh(settings)
    return settings
