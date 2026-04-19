"""Integration tests for the authentication API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_db
from backend.main import create_app
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user


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
async def test_update_me_email(
    client: AsyncClient, admin_user: User, auth_headers: dict, db_session: AsyncSession
) -> None:
    """Authenticated users can update their own email address."""
    response = await client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"email": "updated-admin@test.com"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "updated-admin@test.com"

    await db_session.refresh(admin_user)
    assert admin_user.email == "updated-admin@test.com"


@pytest.mark.asyncio
async def test_update_me_rejects_duplicate_email(
    client: AsyncClient,
    admin_user: User,
    readonly_user: User,
    auth_headers: dict,
) -> None:
    """Users cannot take another account's email address."""
    response = await client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"email": readonly_user.email},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "email_exists",
        "message": "Email already exists",
    }


@pytest.mark.asyncio
async def test_change_my_password_requires_current_password(
    client: AsyncClient,
    admin_user: User,
    auth_headers: dict,
) -> None:
    """The current password must be provided correctly to change it."""
    response = await client.post(
        "/api/auth/me/change-password",
        headers=auth_headers,
        json={
            "current_password": "wrongpassword",
            "new_password": "newsecurepassword123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "invalid_current_password",
        "message": "Current password is incorrect",
    }


@pytest.mark.asyncio
async def test_change_my_password_invalidates_existing_access_token(
    client: AsyncClient,
    admin_user: User,
    auth_headers: dict,
) -> None:
    """Changing a password invalidates tokens issued before the change."""
    response = await client.post(
        "/api/auth/me/change-password",
        headers=auth_headers,
        json={
            "current_password": "adminpassword123",
            "new_password": "newsecurepassword123",
        },
    )

    assert response.status_code == 204

    stale_response = await client.get("/api/auth/me", headers=auth_headers)
    assert stale_response.status_code == 401

    login_response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "newsecurepassword123"},
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_get_me_rejects_access_token_without_iat(
    client: AsyncClient,
    admin_user: User,
) -> None:
    """Access tokens without an iat claim are rejected."""
    settings = get_settings()
    token_without_iat = jwt.encode(
        {"sub": admin_user.username},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token_without_iat}"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_reset_user_password(
    client: AsyncClient,
    admin_user: User,
    readonly_user: User,
    auth_headers: dict,
) -> None:
    """Admin can reset another user's password through the admin-managed flow."""
    response = await client.post(
        f"/api/auth/users/{readonly_user.id}/reset-password",
        headers=auth_headers,
        json={"new_password": "temporaryreset123"},
    )

    assert response.status_code == 204

    old_login = await client.post(
        "/api/auth/login",
        data={"username": "readonly", "password": "readonlypassword123"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/auth/login",
        data={"username": "readonly", "password": "temporaryreset123"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_reset_user_password_requires_admin(
    client: AsyncClient,
    admin_user: User,
    readonly_auth_headers: dict,
) -> None:
    """Only admins can reset another user's password."""
    response = await client.post(
        f"/api/auth/users/{admin_user.id}/reset-password",
        headers=readonly_auth_headers,
        json={"new_password": "temporaryreset123"},
    )

    assert response.status_code == 403


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

    login_response = await client.post(
        "/api/auth/login",
        data={"username": "newuser", "password": "securepassword123"},
    )
    assert login_response.status_code == 200


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


@pytest.mark.asyncio
async def test_list_users_as_admin(
    client: AsyncClient,
    admin_user: User,
    readonly_user: User,
    auth_headers: dict,
) -> None:
    """Admin can list existing user accounts."""
    response = await client.get("/api/auth/users", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert [item["username"] for item in data] == ["admin", "readonly"]


@pytest.mark.asyncio
async def test_list_users_requires_admin(
    client: AsyncClient,
    admin_user: User,
    readonly_user: User,
    readonly_auth_headers: dict,
) -> None:
    """Non-admin users cannot list accounts."""
    response = await client.get("/api/auth/users", headers=readonly_auth_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_requires_admin(
    client: AsyncClient,
    admin_user: User,
    readonly_auth_headers: dict,
) -> None:
    """Non-admin users cannot update user accounts via the admin endpoint."""
    response = await client.patch(
        f"/api/auth/users/{admin_user.id}",
        headers=readonly_auth_headers,
        json={"is_active": False},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_role_and_activation_as_admin(
    client: AsyncClient,
    admin_user: User,
    readonly_user: User,
    auth_headers: dict,
) -> None:
    """Admin can change a user's role and activation status."""
    response = await client.patch(
        f"/api/auth/users/{readonly_user.id}",
        json={"role": "secretaire", "is_active": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "secretaire"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_other_admin_succeeds_when_two_admins_exist(
    client: AsyncClient,
    admin_user: User,
    secondary_admin_user: User,
    auth_headers: dict,
) -> None:
    """One admin can demote another admin while an active admin remains."""
    response = await client.patch(
        f"/api/auth/users/{secondary_admin_user.id}",
        json={"role": "tresorier"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "tresorier"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_last_active_admin_cannot_be_removed(
    db_session: AsyncSession,
    admin_user: User,
) -> None:
    """A synthetic admin context can exercise the last-active-admin guard."""
    app = create_app()

    async def _override_get_db():
        yield db_session

    synthetic_admin = User(
        id=999,
        username="synthetic-admin",
        email="synthetic-admin@test.com",
        password_hash="not-used",
        role=UserRole.ADMIN,
        is_active=True,
    )

    async def _override_get_current_user() -> User:
        return synthetic_admin

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as override_client:
        response = await override_client.patch(
            f"/api/auth/users/{admin_user.id}",
            json={"is_active": False},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "last_admin",
        "message": "At least one active admin must remain",
    }


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_self(
    client: AsyncClient,
    admin_user: User,
    auth_headers: dict,
) -> None:
    """Admin cannot deactivate their own account through admin UI endpoints."""
    response = await client.patch(
        f"/api/auth/users/{admin_user.id}",
        json={"is_active": False},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "self_deactivate",
        "message": "You cannot deactivate your own account",
    }


@pytest.mark.asyncio
async def test_admin_cannot_change_own_role(
    client: AsyncClient,
    admin_user: User,
    auth_headers: dict,
) -> None:
    """Admin cannot remove their own admin role through admin UI endpoints."""
    response = await client.patch(
        f"/api/auth/users/{admin_user.id}",
        json={"role": "tresorier"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "self_demote",
        "message": "You cannot remove your own admin role",
    }
