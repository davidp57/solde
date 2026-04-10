"""Cash register service — journal entries and physical cash counts."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.cash import CashCount, CashMovementType, CashRegister
from backend.schemas.cash import CashCountCreate, CashEntryCreate

# Denomination values in euros
_DENOMINATIONS: dict[str, Decimal] = {
    "count_100": Decimal("100"),
    "count_50": Decimal("50"),
    "count_20": Decimal("20"),
    "count_10": Decimal("10"),
    "count_5": Decimal("5"),
    "count_2": Decimal("2"),
    "count_1": Decimal("1"),
    "count_cents_50": Decimal("0.50"),
    "count_cents_20": Decimal("0.20"),
    "count_cents_10": Decimal("0.10"),
    "count_cents_5": Decimal("0.05"),
    "count_cents_2": Decimal("0.02"),
    "count_cents_1": Decimal("0.01"),
}


async def _current_balance(db: AsyncSession) -> Decimal:
    """Return the current cash register balance (sum of IN - sum of OUT)."""
    result = await db.execute(
        select(func.sum(CashRegister.amount)).where(
            CashRegister.type == CashMovementType.IN
        )
    )
    total_in = result.scalar_one_or_none() or Decimal("0")
    result2 = await db.execute(
        select(func.sum(CashRegister.amount)).where(
            CashRegister.type == CashMovementType.OUT
        )
    )
    total_out = result2.scalar_one_or_none() or Decimal("0")
    return Decimal(str(total_in)) - Decimal(str(total_out))


async def add_cash_entry(db: AsyncSession, payload: CashEntryCreate) -> CashRegister:
    """Add a cash register entry and compute the running balance."""
    balance_before = await _current_balance(db)
    if payload.type == CashMovementType.IN:
        balance_after = balance_before + payload.amount
    else:
        balance_after = balance_before - payload.amount

    entry = CashRegister(
        date=payload.date,
        amount=payload.amount,
        type=payload.type,
        contact_id=payload.contact_id,
        payment_id=payload.payment_id,
        reference=payload.reference,
        description=payload.description,
        balance_after=balance_after,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_cash_entries(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[CashRegister]:
    result = await db.execute(
        select(CashRegister)
        .order_by(CashRegister.date.desc(), CashRegister.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_cash_count(db: AsyncSession, payload: CashCountCreate) -> CashCount:
    """Record a physical cash count and compute the difference vs expected balance."""
    total_counted = sum(
        getattr(payload, field) * value for field, value in _DENOMINATIONS.items()
    )
    balance_expected = await _current_balance(db)
    difference = total_counted - balance_expected

    count = CashCount(
        date=payload.date,
        **{field: getattr(payload, field) for field in _DENOMINATIONS},
        total_counted=total_counted,
        balance_expected=balance_expected,
        difference=difference,
        notes=payload.notes,
    )
    db.add(count)
    await db.commit()
    await db.refresh(count)
    return count


async def list_cash_counts(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[CashCount]:
    result = await db.execute(
        select(CashCount)
        .order_by(CashCount.date.desc(), CashCount.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_cash_balance(db: AsyncSession) -> Decimal:
    return await _current_balance(db)
