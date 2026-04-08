"""Integration tests for the authentication API endpoints."""

import pytest
from httpx import AsyncClient

from backend.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user: User) -> None:
    """Valid credentials return access and refresh tokens."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user: User) -> None:
    """Wrong password returns 401."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient) -> None:
    """Unknown username returns 401."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "nobody", "password": "somepassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    """Authenticated user can retrieve their own profile."""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient) -> None:
    """Unauthenticated request to /me returns 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, admin_user: User) -> None:
    """Valid refresh token returns new token pair."""
    login_response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient) -> None:
    """Invalid refresh token returns 401."""
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": "not.a.valid.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_user_as_admin(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    """Admin can create a new user."""
    response = await client.post(
        "/api/auth/users",
        json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "securepassword123",
            "role": "tresorier",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "tresorier"


@pytest.mark.asyncio
async def test_create_user_duplicate(
    client: AsyncClient, admin_user: User, auth_headers: dict
) -> None:
    """Creating a user with an existing username returns 409."""
    response = await client.post(
        "/api/auth/users",
        json={
            "username": "admin",
            "email": "other@test.com",
            "password": "securepassword123",
            "role": "readonly",
        },
        headers=auth_headers,
    )
    assert response.status_code == 409
