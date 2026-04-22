"""Integration tests for HTTP security headers (BL-047)."""

from httpx import AsyncClient


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
