"""Shared pytest fixtures for all tests."""

# ---------------------------------------------------------------------------
# Speed up bcrypt in tests: reduce rounds from 12 (default, ~250 ms/op) to 4
# (minimum, ~4 ms/op).  Must run before any module calls bcrypt.gensalt().
# ---------------------------------------------------------------------------
import bcrypt as _bcrypt_module

_original_gensalt = _bcrypt_module.gensalt
_bcrypt_module.gensalt = lambda rounds=4, prefix=b"2b": _original_gensalt(
    rounds=rounds, prefix=prefix
)
# ---------------------------------------------------------------------------

import importlib
import pkgutil
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import backend.models
from backend.database import Base, get_db
from backend.models.user import User, UserRole
from backend.services.auth import hash_password

# Register every ORM model on Base.metadata before the session-scoped
# create_all. Discovered rather than listed by hand: a forgotten module would
# only be imported later (e.g. by the routers in create_app()), so its table is
# missing from the schema while the per-test cleanup still tries to empty it.
for _module_info in pkgutil.iter_modules(backend.models.__path__):
    importlib.import_module(f"{backend.models.__name__}.{_module_info.name}")

# In-memory SQLite for tests — StaticPool keeps a single connection alive
# so the database persists across the session-scoped event loop.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_test_session_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_test_schema() -> AsyncGenerator[None, None]:
    """Create all tables once for the entire test session."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_test_data() -> AsyncGenerator[None, None]:
    """Truncate all tables after each test (much faster than DDL create/drop)."""
    yield
    async with _test_engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        await conn.execute(text("PRAGMA foreign_keys=ON"))


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
async def secretaire_user(db_session: AsyncSession) -> User:
    """Create and persist a test secretaire user."""
    user = User(
        username="secretaire",
        email="secretaire@test.com",
        password_hash=hash_password("secretairepassword123"),
        role=UserRole.SECRETAIRE,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def tresorier_user(db_session: AsyncSession) -> User:
    """Create and persist a test tresorier user."""
    user = User(
        username="tresorier",
        email="tresorier@test.com",
        password_hash=hash_password("tresorierpassword123"),
        role=UserRole.TRESORIER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def secondary_admin_user(db_session: AsyncSession) -> User:
    """Create and persist a second test admin user."""
    user = User(
        username="admin2",
        email="admin2@test.com",
        password_hash=hash_password("adminpassword456"),
        role=UserRole.ADMIN,
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


@pytest_asyncio.fixture
async def secretaire_auth_headers(client: AsyncClient, secretaire_user: User) -> dict[str, str]:
    """Return Authorization headers for the secretaire user."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "secretaire", "password": "secretairepassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def tresorier_auth_headers(client: AsyncClient, tresorier_user: User) -> dict[str, str]:
    """Return Authorization headers for the tresorier user."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "tresorier", "password": "tresorierpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
