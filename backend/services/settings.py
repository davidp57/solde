"""Application settings service — read and update the single settings row."""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import Base
from backend.models.app_settings import AppSettings
from backend.models.bank import BankTransaction, BankTransactionSource
from backend.models.cash import CashMovementType, CashRegister
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.schemas.settings import AppSettingsUpdate, SystemOpeningRead, TreasurySystemOpeningRead, TreasurySystemOpeningUpdate

logger = logging.getLogger(__name__)

_SETTINGS_ID = 1
_PRESERVED_TABLES = {"users"}
_SYSTEM_OPENING_DESCRIPTION = "Ouverture du système"


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


def _to_signed_cash_amount(entry: CashRegister | None) -> Decimal | None:
    if entry is None:
        return None
    amount = Decimal(str(entry.amount))
    return amount if entry.type == CashMovementType.IN else -amount


async def _get_default_system_opening_date(db: AsyncSession) -> date | None:
    result = await db.execute(select(FiscalYear.start_date).order_by(FiscalYear.start_date.asc()))
    return result.scalars().first()


async def get_treasury_system_opening(db: AsyncSession) -> TreasurySystemOpeningRead:
    default_date = await _get_default_system_opening_date(db)
    bank_entry = (
        await db.execute(
            select(BankTransaction)
            .where(BankTransaction.source == BankTransactionSource.SYSTEM_OPENING)
            .order_by(BankTransaction.date.asc(), BankTransaction.id.asc())
        )
    ).scalars().first()
    cash_entry = (
        await db.execute(
            select(CashRegister)
            .where(CashRegister.description == _SYSTEM_OPENING_DESCRIPTION)
            .order_by(CashRegister.date.asc(), CashRegister.id.asc())
        )
    ).scalars().first()

    return TreasurySystemOpeningRead(
        default_date=default_date,
        bank=SystemOpeningRead(
            configured=bank_entry is not None,
            date=bank_entry.date if bank_entry is not None else None,
            amount=Decimal(str(bank_entry.amount)) if bank_entry is not None else None,
            reference=bank_entry.reference if bank_entry is not None else None,
        ),
        cash=SystemOpeningRead(
            configured=cash_entry is not None,
            date=cash_entry.date if cash_entry is not None else None,
            amount=_to_signed_cash_amount(cash_entry),
            reference=cash_entry.reference if cash_entry is not None else None,
        ),
    )


async def upsert_treasury_system_opening(
    db: AsyncSession, payload: TreasurySystemOpeningUpdate
) -> TreasurySystemOpeningRead:
    from backend.services.bank_service import recompute_bank_balances
    from backend.services.cash_service import recompute_cash_balances

    bank_entries = (
        await db.execute(
            select(BankTransaction)
            .where(BankTransaction.source == BankTransactionSource.SYSTEM_OPENING)
            .order_by(BankTransaction.id.asc())
        )
    ).scalars().all()
    cash_entries = (
        await db.execute(
            select(CashRegister)
            .where(CashRegister.description == _SYSTEM_OPENING_DESCRIPTION)
            .order_by(CashRegister.id.asc())
        )
    ).scalars().all()

    bank_entry = bank_entries[0] if bank_entries else None
    cash_entry = cash_entries[0] if cash_entries else None

    for extra_entry in bank_entries[1:]:
        await db.delete(extra_entry)
    for extra_entry in cash_entries[1:]:
        await db.delete(extra_entry)

    if bank_entry is None:
        bank_entry = BankTransaction(
            date=payload.bank.date,
            amount=payload.bank.amount,
            reference=payload.bank.reference,
            description=_SYSTEM_OPENING_DESCRIPTION,
            balance_after=Decimal("0"),
            source=BankTransactionSource.SYSTEM_OPENING,
        )
        db.add(bank_entry)
    else:
        bank_entry.date = payload.bank.date
        bank_entry.amount = payload.bank.amount
        bank_entry.reference = payload.bank.reference
        bank_entry.description = _SYSTEM_OPENING_DESCRIPTION
        bank_entry.source = BankTransactionSource.SYSTEM_OPENING

    cash_amount = abs(payload.cash.amount)
    cash_type = CashMovementType.IN if payload.cash.amount > 0 else CashMovementType.OUT
    if cash_entry is None:
        cash_entry = CashRegister(
            date=payload.cash.date,
            amount=cash_amount,
            type=cash_type,
            reference=payload.cash.reference,
            description=_SYSTEM_OPENING_DESCRIPTION,
            balance_after=Decimal("0"),
        )
        db.add(cash_entry)
    else:
        cash_entry.date = payload.cash.date
        cash_entry.amount = cash_amount
        cash_entry.type = cash_type
        cash_entry.reference = payload.cash.reference
        cash_entry.description = _SYSTEM_OPENING_DESCRIPTION

    await db.flush()
    await recompute_bank_balances(db)
    await recompute_cash_balances(db)
    await db.commit()

    return await get_treasury_system_opening(db)


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
