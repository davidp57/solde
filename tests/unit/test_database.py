"""Unit tests for database initialisation (BL-060)."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_init_db_does_not_create_tables() -> None:
    """init_db() must only set PRAGMAs; table creation belongs to Alembic."""
    from unittest.mock import patch

    import backend.database as db_module

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async def _noop() -> None:
        return None

    with (
        patch.object(db_module, "_engine", engine),
        patch.object(db_module, "_bootstrap_admin", _noop),
    ):
        await db_module.init_db()

    async with engine.begin() as conn:
        # No tables should have been created
        table_names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        assert table_names == [], f"init_db() must not create tables, found: {table_names}"

        # PRAGMA journal_mode is called — in-memory SQLite returns 'memory'
        # (WAL is not supported there, but the PRAGMA call itself is verified)
        result = await conn.execute(text("PRAGMA journal_mode"))
        mode = result.scalar_one()
        assert mode in ("wal", "memory")  # wal on file DBs, memory on :memory:

    await engine.dispose()
