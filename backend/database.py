"""Database engine and session management (async SQLite with WAL mode)."""

import logging
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
    return create_async_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False},
    )


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
            accounting_entry,
            accounting_rule,
            app_settings,
            bank,
            cash,
            contact,
            fiscal_year,
            import_log,
            invoice,
            payment,
            salary,
            user,
        )

        await conn.run_sync(Base.metadata.create_all)

    await _bootstrap_admin()


async def _bootstrap_admin() -> None:
    """Create the default admin user on first startup if no user exists."""
    from sqlalchemy import select

    from backend.config import get_settings
    from backend.models.user import User, UserRole
    from backend.services.auth import hash_password

    cfg = get_settings()
    async with get_session() as session:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # At least one user exists, nothing to do

        user = User(
            username=cfg.admin_username,
            email=cfg.admin_email,
            password_hash=hash_password(cfg.admin_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(user)
        logging.getLogger(__name__).warning(
            "Bootstrap: created admin user '%s' — change the password immediately!",
            cfg.admin_username,
        )


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
