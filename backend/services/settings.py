"""Application settings service — read and update the single settings row."""

import logging
from datetime import date
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import Base
from backend.models.app_settings import AppSettings
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.schemas.settings import AppSettingsUpdate

logger = logging.getLogger(__name__)

_SETTINGS_ID = 1
_PRESERVED_TABLES = {"users"}


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


# ---------------------------------------------------------------------------
# Database reset (test/demo helper)
# ---------------------------------------------------------------------------


async def reset_data(db: AsyncSession) -> dict[str, int]:
    """Delete every application table except users.

    Returns a mapping of table name → number of rows deleted.
    """
    deleted: dict[str, int] = {}

    for table in reversed(Base.metadata.sorted_tables):
        if table.name in _PRESERVED_TABLES:
            continue
        result = cast(CursorResult[Any], await db.execute(delete(table)))
        deleted[table.name] = result.rowcount or 0
        logger.debug("reset_data: deleted %d rows from %s", deleted[table.name], table.name)

    await db.commit()
    db.expunge_all()
    logger.info("reset_data: database reset completed while preserving users only")
    return deleted


async def bootstrap_accounting_setup(db: AsyncSession) -> dict[str, int]:
    """Seed accounts, rules, and the replay fiscal years used in local testing."""
    from backend.services.accounting_account import seed_default_accounts
    from backend.services.accounting_engine import seed_default_rules

    accounts_inserted = await seed_default_accounts(db)
    rules_inserted = await seed_default_rules(db)

    existing_names = {
        name for (name,) in (await db.execute(select(FiscalYear.name))).all() if name is not None
    }
    fiscal_years_created = 0
    for name, start_date, end_date in [
        ("2023", date(2023, 8, 1), date(2024, 7, 31)),
        ("2024", date(2024, 8, 1), date(2025, 7, 31)),
        ("2025", date(2025, 8, 1), date(2026, 7, 31)),
    ]:
        if name in existing_names:
            continue
        db.add(
            FiscalYear(
                name=name,
                start_date=start_date,
                end_date=end_date,
                status=FiscalYearStatus.OPEN,
            )
        )
        fiscal_years_created += 1

    if fiscal_years_created:
        await db.commit()

    return {
        "accounts_inserted": accounts_inserted,
        "rules_inserted": rules_inserted,
        "fiscal_years_created": fiscal_years_created,
    }
