"""Application settings service — read and update the single settings row."""

import logging
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry
from backend.models.app_settings import AppSettings
from backend.models.bank import BankTransaction, Deposit
from backend.models.cash import CashCount, CashRegister
from backend.models.contact import Contact
from backend.models.import_log import ImportLog
from backend.models.invoice import Invoice, InvoiceLine
from backend.models.payment import Payment
from backend.models.salary import Salary
from backend.schemas.settings import AppSettingsUpdate

logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# Database reset (test/demo helper)
# ---------------------------------------------------------------------------

# Tables cleared in FK-safe order; users, app_settings, accounting_accounts,
# accounting_rules and fiscal_years are intentionally preserved.
_RESET_ORDER: list[type] = [
    ImportLog,
    Payment,
    InvoiceLine,
    Invoice,
    Salary,
    AccountingEntry,
    CashRegister,
    CashCount,
    BankTransaction,
    Deposit,
    Contact,
]


async def reset_data(db: AsyncSession) -> dict[str, int]:
    """Delete all transactional data while preserving users, settings, chart of accounts
    and accounting rules.

    Returns a mapping of table name → number of rows deleted.
    """
    deleted: dict[str, int] = {}
    for model in _RESET_ORDER:
        result = cast(CursorResult[Any], await db.execute(delete(model)))
        table = model.__tablename__  # type: ignore[attr-defined]
        deleted[table] = result.rowcount
        logger.info("reset_data: deleted %d rows from %s", result.rowcount, table)

    await db.commit()
    logger.warning("reset_data: database reset completed by request")
    return deleted
