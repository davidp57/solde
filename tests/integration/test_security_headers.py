"""Integration tests for security headers (BL-047) and CORS configuration (BL-055)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from fastapi import FastAPI


async def test_security_headers_present_on_api_response(
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """All API responses should include baseline security headers."""
    response = await client.get("/api/settings/", headers=auth_headers)

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-xss-protection"] == "1; mode=block"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


async def test_security_headers_on_unauthenticated_response(
    client: AsyncClient,
) -> None:
    """Security headers should be present even on 401 responses."""
    response = await client.get("/api/settings/")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


# ---------------------------------------------------------------------------
# BL-055: CORS origins configurable via settings
# ---------------------------------------------------------------------------


def _make_cors_app(cors_allowed_origins: list[str], debug: bool) -> FastAPI:
    """Return a minimal FastAPI app with only CORSMiddleware, mirroring main.py logic."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()
    _origins = cors_allowed_origins or (["*"] if debug else [])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {}

    return app


async def test_cors_explicit_origins_respected() -> None:
    """When cors_allowed_origins is set, CORS uses those origins exclusively."""
    explicit_origin = "https://app.exemple.fr"
    app = _make_cors_app(cors_allowed_origins=[explicit_origin], debug=False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.options(
            "/ping",
            headers={"Origin": explicit_origin, "Access-Control-Request-Method": "GET"},
        )

    assert response.headers.get("access-control-allow-origin") == explicit_origin


async def test_cors_wildcard_in_debug_mode_when_no_origins_configured() -> None:
    """When cors_allowed_origins is empty and debug=True, wildcard '*' is used."""
    app = _make_cors_app(cors_allowed_origins=[], debug=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/ping", headers={"Origin": "http://localhost:5173"})

    assert response.headers.get("access-control-allow-origin") in ("*", "http://localhost:5173")


async def test_cors_empty_in_production_when_no_origins_configured() -> None:
    """When cors_allowed_origins is empty and debug=False, no CORS headers are sent."""
    app = _make_cors_app(cors_allowed_origins=[], debug=False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/ping", headers={"Origin": "https://attacker.exemple.com"})

    assert "access-control-allow-origin" not in response.headers
