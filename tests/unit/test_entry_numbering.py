"""Entry numbers allocated by two concurrent sessions never collide (issue #164).

The shared in-memory database of the rest of the suite has a single connection,
so it cannot show two writers: this test runs on a SQLite file with a real pool.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.database import Base
from backend.models.accounting_entry import AccountingEntry
from backend.services.accounting_engine import next_entry_number, next_entry_numbers


@pytest_asyncio.fixture
async def file_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'numbers.db').as_posix()}")
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


def _entry(number: str) -> AccountingEntry:
    return AccountingEntry(
        entry_number=number,
        date=date(2026, 1, 1),
        account_number="512000",
        label="x",
        debit=Decimal("1"),
        credit=Decimal("0"),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("allocate", ["single", "batch"])
async def test_a_second_writer_waits_for_the_first_one_to_commit(
    file_engine: AsyncEngine, allocate: str
) -> None:
    factory = async_sessionmaker(file_engine, class_=AsyncSession, expire_on_commit=False)

    async def _allocate(db: AsyncSession) -> str:
        if allocate == "single":
            return await next_entry_number(db)
        return (await next_entry_numbers(db, 1))[0]

    async with factory() as first, factory() as second:
        first_number = await _allocate(first)
        first.add(_entry(first_number))
        await first.flush()

        async def _second() -> str:
            number = await _allocate(second)
            second.add(_entry(number))
            await second.commit()
            return number

        pending = asyncio.create_task(_second())
        await asyncio.sleep(0.3)
        # Reading MAX(entry_number) now would hand out the number the first
        # session is about to commit.
        assert not pending.done()

        await first.commit()
        second_number = await asyncio.wait_for(pending, timeout=5)

    assert (first_number, second_number) == ("000001", "000002")
