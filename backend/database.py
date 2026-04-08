"""Database engine and session management (async SQLite with WAL mode)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""

    pass


def _build_engine(database_url: str | None = None) -> AsyncEngine:
    """Create async SQLAlchemy engine with WAL journal mode."""
    url = database_url or get_settings().database_url
    engine = create_async_engine(
        url,
        echo=get_settings().debug,
        connect_args={"check_same_thread": False},
    )
    return engine


# Module-level engine and session factory
_engine = _build_engine()
_async_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Create all tables and enable WAL mode. Called at application startup."""
    async with _engine.begin() as conn:
        # Enable WAL mode for better concurrent read performance
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        from backend.models import (  # noqa: F401
            accounting_account,
            app_settings,
            contact,
            invoice,
            user,
        )

        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager providing a database session."""
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with get_session() as session:
        yield session
