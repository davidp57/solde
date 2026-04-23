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


def _make_settings(*, debug: bool):
    """Build a Settings instance with the given debug flag."""
    from backend.config import Settings

    return Settings(
        debug=debug,
        jwt_secret_key="test-secret-key-for-testing-only-1234567890",
        database_url="sqlite+aiosqlite:///:memory:",
    )
