"""Integration tests for BL-046: refresh token stored in HttpOnly cookie."""

import pytest
from httpx import AsyncClient

from backend.models.user import User


@pytest.mark.asyncio
async def test_login_sets_refresh_token_cookie(client: AsyncClient, admin_user: User) -> None:
    """Login should set refresh_token as an HttpOnly cookie."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword123"},
    )
    assert response.status_code == 200

    # Cookie must be present
    cookie = response.cookies.get("refresh_token")
    assert cookie is not None

    # JSON body must NOT contain refresh_token
    data = response.json()
    assert "refresh_token" not in data
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_cookie_attributes(client: AsyncClient, admin_user: User) -> None:
    """The refresh_token cookie should have HttpOnly, SameSite=Strict, Path=/api/auth."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword123"},
    )

    # httpx stores raw Set-Cookie headers
    raw_cookies = response.headers.get_list("set-cookie")
    refresh_cookie = next(
        (c for c in raw_cookies if c.startswith("refresh_token=")),
        None,
    )
    assert refresh_cookie is not None
    lower = refresh_cookie.lower()
    assert "httponly" in lower
    assert "samesite=strict" in lower
    assert "path=/api/auth" in lower


@pytest.mark.asyncio
async def test_refresh_reads_cookie_and_returns_new_cookie(
    client: AsyncClient,
    admin_user: User,
) -> None:
    """POST /auth/refresh should read the refresh_token from the cookie."""
    # Login to get cookie
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword123"},
    )
    assert login_resp.status_code == 200
    refresh_cookie = login_resp.cookies.get("refresh_token")
    assert refresh_cookie is not None

    # Refresh — explicitly pass the cookie
    refresh_resp = await client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_cookie},
    )
    assert refresh_resp.status_code == 200

    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" not in data

    # New cookie should be set
    new_cookie = refresh_resp.cookies.get("refresh_token")
    assert new_cookie is not None


@pytest.mark.asyncio
async def test_refresh_without_cookie_returns_401(client: AsyncClient) -> None:
    """POST /auth/refresh without a cookie returns 401."""
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_refresh_cookie(
    client: AsyncClient,
    admin_user: User,
) -> None:
    """POST /auth/logout should clear the refresh_token cookie."""
    # Login
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword123"},
    )
    token = login_resp.json()["access_token"]

    # Logout
    logout_resp = await client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        cookies={"refresh_token": login_resp.cookies.get("refresh_token") or ""},
    )
    assert logout_resp.status_code == 204

    # Cookie should be cleared (expired or deleted)
    raw_cookies = logout_resp.headers.get_list("set-cookie")
    refresh_cookie = next(
        (c for c in raw_cookies if c.startswith("refresh_token=")),
        None,
    )
    assert refresh_cookie is not None
    # The cookie should have max-age=0 or an empty value to expire it
    lower = refresh_cookie.lower()
    assert "max-age=0" in lower or 'refresh_token=""' in lower or "refresh_token=;" in lower


@pytest.mark.asyncio
async def test_refresh_updates_must_change_password(
    client: AsyncClient,
    admin_user: User,
) -> None:
    """Refresh response should include must_change_password from user state."""
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword123"},
    )
    assert login_resp.status_code == 200
    refresh_cookie = login_resp.cookies.get("refresh_token")

    refresh_resp = await client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_cookie or ""},
    )
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["must_change_password"] is False
