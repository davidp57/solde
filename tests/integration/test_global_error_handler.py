"""Tests for the global exception handler in main.py."""

import logging
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.main import create_app


def _build_app_with_broken_route(db_session: AsyncSession | None = None) -> tuple:
    """Return (app, client_factory) with a /api/test-explosion route that always raises."""
    app = create_app()

    async def _explode() -> None:
        raise RuntimeError("Unexpected kaboom")

    # Insert BEFORE the static‐files mount (last entry) so it isn't shadowed.
    app.router.routes.insert(0, APIRoute("/api/test-explosion", _explode))

    if db_session is not None:

        async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield db_session

        app.dependency_overrides[get_db] = _override_get_db

    return app


@pytest_asyncio.fixture
async def broken_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield a test client whose app has a route that always raises RuntimeError."""
    app = _build_app_with_broken_route(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ----- 500 — unhandled exception -----


@pytest.mark.asyncio
async def test_unhandled_exception_returns_json_500(broken_client: AsyncClient) -> None:
    """An unhandled exception must return a structured JSON 500."""
    resp = await broken_client.get("/api/test-explosion")

    assert resp.status_code == 500
    body = resp.json()
    assert "detail" in body
    # Must NOT contain the traceback / internal info
    assert "kaboom" not in body["detail"].lower()
    assert "traceback" not in resp.text.lower()


@pytest.mark.asyncio
async def test_unhandled_exception_includes_error_code(broken_client: AsyncClient) -> None:
    """The JSON 500 response must include an error code for client-side handling."""
    resp = await broken_client.get("/api/test-explosion")

    body = resp.json()
    assert body.get("code") == "INTERNAL_SERVER_ERROR"


# ----- 422 — request validation error -----


@pytest.mark.asyncio
async def test_validation_error_returns_422_json(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """A request validation error must return structured JSON, not a bare Pydantic dump."""
    # fy_id path param must be int — passing a string triggers RequestValidationError
    resp = await client.get("/api/accounting/fiscal-years/not-a-number", headers=auth_headers)
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body


# ----- HTTPException pass-through -----


@pytest.mark.asyncio
async def test_http_exception_still_works(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """Existing HTTPException handling (e.g. 404) must be preserved unchanged."""
    resp = await client.get("/api/contacts/99999", headers=auth_headers)
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body


# ----- logging -----


@pytest.mark.asyncio
async def test_exception_handler_logs_error(
    broken_client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    """The global handler must log the full exception for debugging."""
    backend_logger = logging.getLogger("backend")
    backend_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.ERROR, logger="backend"):
            resp = await broken_client.get("/api/test-explosion")
    finally:
        backend_logger.removeHandler(caplog.handler)

    assert resp.status_code == 500
    assert "Unexpected kaboom" in caplog.text
