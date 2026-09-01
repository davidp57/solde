"""Tests for OpenAPI/Swagger conditional exposure (BL-068)."""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_swagger_available_in_debug_mode() -> None:
    """When debug=True, /api/docs and /api/openapi.json must be reachable."""
    with patch("backend.main.get_settings") as mock_settings:
        mock_settings.return_value = _make_settings(debug=True)
        from backend.main import create_app

        app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp_docs = await ac.get("/api/docs")
        resp_redoc = await ac.get("/api/redoc")
        resp_openapi = await ac.get("/api/openapi.json")

    assert resp_docs.status_code == 200
    assert resp_redoc.status_code == 200
    assert resp_openapi.status_code == 200


@pytest.mark.asyncio
async def test_swagger_disabled_in_production() -> None:
    """When debug=False, /api/docs, /api/redoc and /api/openapi.json must return 404."""
    with patch("backend.main.get_settings") as mock_settings:
        mock_settings.return_value = _make_settings(debug=False)
        from backend.main import create_app

        app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp_docs = await ac.get("/api/docs")
        resp_redoc = await ac.get("/api/redoc")
        resp_openapi = await ac.get("/api/openapi.json")

    assert resp_docs.status_code == 404
    assert resp_redoc.status_code == 404
    assert resp_openapi.status_code == 404


@pytest.mark.asyncio
async def test_swagger_flag_exposes_docs_outside_debug() -> None:
    """`SWAGGER_ENABLED` opens the docs on its own — the other half of `flag or debug`."""
    with patch("backend.main.get_settings") as mock_settings:
        mock_settings.return_value = _make_settings(debug=False, swagger_enabled=True)
        from backend.main import create_app

        app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp_docs = await ac.get("/api/docs")
        resp_openapi = await ac.get("/api/openapi.json")

    assert resp_docs.status_code == 200
    assert resp_openapi.status_code == 200


def _make_settings(*, debug: bool, swagger_enabled: bool = False):
    """Build a Settings instance isolated from the developer's own configuration.

    ``_env_file=None`` keeps pydantic-settings from reading the repository's `.env`,
    and both flags that drive the exposure are passed explicitly — init arguments win
    over environment variables. Without this the outcome depended on whoever ran the
    suite: a local `.env` carrying ``SWAGGER_ENABLED=true`` made the production case
    fail, since `main.create_app` exposes the docs on ``swagger_enabled or debug``.
    """
    from backend.config import Settings

    return Settings(
        _env_file=None,
        debug=debug,
        swagger_enabled=swagger_enabled,
        jwt_secret_key="test-secret-key-for-testing-only-1234567890",
        database_url="sqlite+aiosqlite:///:memory:",
    )
