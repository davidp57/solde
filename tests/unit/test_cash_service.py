"""Unit tests for the cash service — journal entries and cash counts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.cash import CashMovementType
from backend.schemas.cash import CashCountCreate, CashEntryCreate
from backend.services import cash_service

# ---------------------------------------------------------------------------
# Cash entries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_cash_entry_in(db_session: AsyncSession) -> None:
    """Adding an IN entry creates the record with correct balance_after."""
    payload = CashEntryCreate(
        date=date(2024, 3, 1),
        amount=Decimal("100.00"),
        type=CashMovementType.IN,
        description="Encaissement chèque",
    )
    entry = await cash_service.add_cash_entry(db_session, payload)

    assert entry.id is not None
    assert entry.amount == Decimal("100.00")
    assert entry.type == CashMovementType.IN
    assert entry.balance_after == Decimal("100.00")


@pytest.mark.asyncio
async def test_add_cash_entry_out_reduces_balance(db_session: AsyncSession) -> None:
    """An OUT entry reduces the running balance."""
    await cash_service.add_cash_entry(
        db_session,
        CashEntryCreate(
            date=date(2024, 3, 1),
            amount=Decimal("200.00"),
            type=CashMovementType.IN,
        ),
    )
    entry = await cash_service.add_cash_entry(
        db_session,
        CashEntryCreate(
            date=date(2024, 3, 2),
            amount=Decimal("50.00"),
            type=CashMovementType.OUT,
            description="Achat fournitures",
        ),
    )
    assert entry.balance_after == Decimal("150.00")


@pytest.mark.asyncio
async def test_get_balance_empty(db_session: AsyncSession) -> None:
    """Balance is zero when there are no entries."""
    balance = await cash_service.get_cash_balance(db_session)
    assert balance == Decimal("0")


@pytest.mark.asyncio
async def test_get_balance_after_entries(db_session: AsyncSession) -> None:
    """Balance reflects total IN minus total OUT."""
    for amount, movement_type in [
        (Decimal("300.00"), CashMovementType.IN),
        (Decimal("80.00"), CashMovementType.OUT),
        (Decimal("50.00"), CashMovementType.IN),
    ]:
        await cash_service.add_cash_entry(
            db_session,
            CashEntryCreate(date=date(2024, 3, 1), amount=amount, type=movement_type),
        )

    balance = await cash_service.get_cash_balance(db_session)
    assert balance == Decimal("270.00")  # 300 + 50 - 80


@pytest.mark.asyncio
async def test_list_cash_entries_ordered(db_session: AsyncSession) -> None:
    """Entries are returned in reverse chronological order."""
    for d, amount in [
        (date(2024, 1, 1), Decimal("10.00")),
        (date(2024, 2, 1), Decimal("20.00")),
        (date(2024, 3, 1), Decimal("30.00")),
    ]:
        await cash_service.add_cash_entry(
            db_session,
            CashEntryCreate(date=d, amount=amount, type=CashMovementType.IN),
        )

    entries = await cash_service.list_cash_entries(db_session)
    assert entries[0].date > entries[-1].date


@pytest.mark.asyncio
async def test_list_cash_entries_pagination(db_session: AsyncSession) -> None:
    for i in range(5):
        await cash_service.add_cash_entry(
            db_session,
            CashEntryCreate(
                date=date(2024, 1, i + 1),
                amount=Decimal("10.00"),
                type=CashMovementType.IN,
            ),
        )

    page = await cash_service.list_cash_entries(db_session, skip=2, limit=2)
    assert len(page) == 2


# ---------------------------------------------------------------------------
# Cash counts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_cash_count_total(db_session: AsyncSession) -> None:
    """Cash count total is computed from denomination counts."""
    payload = CashCountCreate(
        date=date(2024, 3, 1),
        count_100=1,  # 100.00
        count_20=2,  # 40.00
        count_2=3,  # 6.00
        count_cents_50=4,  # 2.00
    )
    count = await cash_service.create_cash_count(db_session, payload)
    # 100 + 40 + 6 + 2 = 148.00
    assert count.total_counted == Decimal("148.00")


@pytest.mark.asyncio
async def test_create_cash_count_difference(db_session: AsyncSession) -> None:
    """Difference = total_counted - balance_expected."""
    await cash_service.add_cash_entry(
        db_session,
        CashEntryCreate(date=date(2024, 3, 1), amount=Decimal("100.00"), type=CashMovementType.IN),
    )

    payload = CashCountCreate(date=date(2024, 3, 2), count_100=1)  # 100.00 counted
    count = await cash_service.create_cash_count(db_session, payload)

    assert count.balance_expected == Decimal("100.00")
    assert count.difference == Decimal("0.00")


@pytest.mark.asyncio
async def test_create_cash_count_negative_difference(db_session: AsyncSession) -> None:
    """Negative difference when counted amount is less than expected."""
    await cash_service.add_cash_entry(
        db_session,
        CashEntryCreate(date=date(2024, 3, 1), amount=Decimal("100.00"), type=CashMovementType.IN),
    )

    payload = CashCountCreate(date=date(2024, 3, 2), count_50=1)  # only 50.00 counted
    count = await cash_service.create_cash_count(db_session, payload)

    assert count.difference == Decimal("-50.00")


@pytest.mark.asyncio
async def test_list_cash_counts_ordered(db_session: AsyncSession) -> None:
    for d in [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)]:
        await cash_service.create_cash_count(db_session, CashCountCreate(date=d))

    counts = await cash_service.list_cash_counts(db_session)
    assert counts[0].date >= counts[-1].date
