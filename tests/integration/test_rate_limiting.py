"""Integration tests for login rate limiting (BL-045)."""

from unittest.mock import patch

from httpx import AsyncClient

from backend.services.rate_limiter import RateLimiter


async def test_login_returns_429_after_too_many_failed_attempts(
    client: AsyncClient,
    admin_user: object,
) -> None:
    """After exceeding failed login attempts, further attempts return 429."""
    test_limiter = RateLimiter(max_attempts=2, window_seconds=300)

    with patch("backend.routers.auth.login_limiter", test_limiter):
        # Two failed attempts
        for _ in range(2):
            response = await client.post(
                "/api/auth/login",
                data={"username": "admin", "password": "wrongpassword"},
            )
            assert response.status_code == 401

        # Third attempt should be rate limited
        response = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 429
        assert "too many" in response.json()["detail"].lower()


async def test_successful_login_resets_rate_limit(
    client: AsyncClient,
    admin_user: object,
) -> None:
    """A successful login clears the rate limit counter."""
    test_limiter = RateLimiter(max_attempts=3, window_seconds=300)

    with patch("backend.routers.auth.login_limiter", test_limiter):
        # Two failed attempts
        for _ in range(2):
            await client.post(
                "/api/auth/login",
                data={"username": "admin", "password": "wrong"},
            )

        # Successful login
        response = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpassword123"},
        )
        assert response.status_code == 200

        # Counter should be reset — can fail again without 429
        response = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401
