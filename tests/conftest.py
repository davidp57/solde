"""Shared pytest fixtures for all tests."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database import Base, get_db
from backend.models import (
    accounting_account as _acct_module,
)
from backend.models import (
    accounting_entry as _entry_module,
)
from backend.models import (
    accounting_rule as _rule_module,
)
from backend.models import (
    app_settings,
)
from backend.models import (
    bank as _bank_module,
)
from backend.models import (
    cash as _cash_module,
)
from backend.models import (
    contact as _contact_module,
)
from backend.models import (
    fiscal_year as _fy_module,
)
from backend.models import (
    import_log as _import_log_module,
)
from backend.models import (
    invoice as _invoice_module,
)
from backend.models import (
    payment as _payment_module,
)
from backend.models import (
    salary as _salary_module,
)
from backend.models import (
    user as _user_module,
)
from backend.models.user import User, UserRole
from backend.services.auth import hash_password

_REGISTERED_MODEL_MODULES = (
    _acct_module,
    _entry_module,
    _rule_module,
    app_settings,
    _bank_module,
    _cash_module,
    _contact_module,
    _fy_module,
    _import_log_module,
    _invoice_module,
    _payment_module,
    _salary_module,
    _user_module,
)

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_test_session_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test and drop them after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session with rollback after test."""
    async with _test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an async HTTP test client wired to the test DB."""
    from backend.main import create_app

    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create and persist a test admin user."""
    user = User(
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def readonly_user(db_session: AsyncSession) -> User:
    """Create and persist a test readonly user."""
    user = User(
        username="readonly",
        email="readonly@test.com",
        password_hash=hash_password("readonlypassword123"),
        role=UserRole.READONLY,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, admin_user: User) -> dict[str, str]:
    """Return Authorization headers for the admin user."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def readonly_auth_headers(client: AsyncClient, readonly_user: User) -> dict[str, str]:
    """Return Authorization headers for the readonly user."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "readonly", "password": "readonlypassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
