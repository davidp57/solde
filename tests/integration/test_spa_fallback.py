"""Tests for the SPA catch-all route that serves the built frontend."""

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

_INDEX = b"<!doctype html><title>index</title>"
_ASSET = b"console.log('asset');"
_SECRET = b"SECRET-OUTSIDE-DIST"


async def _raw_get(app: Any, path: str) -> tuple[int, dict[bytes, bytes], bytes]:
    """Send a GET with ``path`` verbatim, as Uvicorn hands it over after
    percent-decoding — an HTTP client would normalise the dot segments away."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"test")],
        "client": ("testclient", 50000),
        "server": ("test", 80),
    }
    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start["status"], dict(start["headers"]), body


@pytest.fixture
def spa_app(tmp_path: Path) -> tuple[Any, Path]:
    """App whose frontend dist lives in ``tmp_path/app/frontend/dist``, with a
    secret file two levels above it, where ``data/`` sits in the container."""
    dist = tmp_path / "app" / "frontend" / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_bytes(_INDEX)
    (dist / "assets" / "app.js").write_bytes(_ASSET)
    secret = tmp_path / "app" / "data" / "solde.db"
    secret.parent.mkdir(parents=True)
    secret.write_bytes(_SECRET)

    with patch("backend.main.FRONTEND_DIST", dist):
        from backend.main import create_app

        app = create_app()
    return app, secret


@pytest.mark.asyncio
async def test_existing_asset_is_served_with_immutable_cache(spa_app: tuple[Any, Path]) -> None:
    app, _ = spa_app
    status, headers, body = await _raw_get(app, "/assets/app.js")
    assert status == 200
    assert body == _ASSET
    assert b"immutable" in headers[b"cache-control"]


@pytest.mark.asyncio
async def test_client_route_falls_back_to_index(spa_app: tuple[Any, Path]) -> None:
    app, _ = spa_app
    status, headers, body = await _raw_get(app, "/invoices/42")
    assert status == 200
    assert body == _INDEX
    assert b"no-store" in headers[b"cache-control"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/../../data/solde.db",
        "/assets/../../../data/solde.db",
        "/assets/..\\..\\..\\data\\solde.db",
    ],
)
async def test_path_traversal_never_serves_files_outside_dist(
    spa_app: tuple[Any, Path], path: str
) -> None:
    app, _ = spa_app
    status, _, body = await _raw_get(app, path)
    assert _SECRET not in body
    assert status == 200
    assert body == _INDEX


@pytest.mark.asyncio
async def test_absolute_path_never_serves_files_outside_dist(spa_app: tuple[Any, Path]) -> None:
    app, secret = spa_app
    status, _, body = await _raw_get(app, "/" + secret.as_posix())
    assert _SECRET not in body
    assert status == 200
    assert body == _INDEX
