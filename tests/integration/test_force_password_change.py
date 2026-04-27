"""Integration tests for BL-053: force password change on first login."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User, UserRole
from backend.services.auth import hash_password


@pytest.fixture
async def must_change_user(db_session: AsyncSession) -> User:
    """Create a user with must_change_password=True."""
    user = User(
        username="newuser",
        email="newuser@test.com",
        password_hash=hash_password("temporarypass1"),
        role=UserRole.TRESORIER,
        is_active=True,
        must_change_password=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _login(client: AsyncClient, username: str, password: str) -> dict:
    """Helper: login and return the full response JSON."""
    response = await client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()


class TestLoginResponseIncludesMustChangePassword:
    @pytest.mark.asyncio
    async def test_login_returns_must_change_password_false_for_normal_user(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        data = await _login(client, "admin", "adminpassword123")
        assert data["must_change_password"] is False

    @pytest.mark.asyncio
    async def test_login_returns_must_change_password_true_when_flag_set(
        self, client: AsyncClient, must_change_user: User
    ) -> None:
        data = await _login(client, "newuser", "temporarypass1")
        assert data["must_change_password"] is True


class TestMustChangePasswordBlocksNormalEndpoints:
    @pytest.mark.asyncio
    async def test_blocked_user_cannot_access_contacts(
        self, client: AsyncClient, must_change_user: User
    ) -> None:
        tokens = await _login(client, "newuser", "temporarypass1")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = await client.get("/api/contacts/", headers=headers)
        assert response.status_code == 403
        assert "password" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_blocked_user_cannot_access_dashboard(
        self, client: AsyncClient, must_change_user: User
    ) -> None:
        tokens = await _login(client, "newuser", "temporarypass1")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = await client.get("/api/dashboard/summary", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_blocked_user_can_access_auth_me(
        self, client: AsyncClient, must_change_user: User
    ) -> None:
        tokens = await _login(client, "newuser", "temporarypass1")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["must_change_password"] is True

    @pytest.mark.asyncio
    async def test_blocked_user_can_change_password(
        self, client: AsyncClient, must_change_user: User
    ) -> None:
        tokens = await _login(client, "newuser", "temporarypass1")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = await client.post(
            "/api/auth/me/change-password",
            headers=headers,
            json={"current_password": "temporarypass1", "new_password": "newSecurePass8"},
        )
        assert response.status_code == 204


class TestPasswordChangeClearsFlag:
    @pytest.mark.asyncio
    async def test_changing_password_clears_must_change_password(
        self, client: AsyncClient, must_change_user: User, db_session: AsyncSession
    ) -> None:
        tokens = await _login(client, "newuser", "temporarypass1")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        await client.post(
            "/api/auth/me/change-password",
            headers=headers,
            json={"current_password": "temporarypass1", "new_password": "newSecurePass8"},
        )

        # Re-login with new password
        new_tokens = await _login(client, "newuser", "newSecurePass8")
        assert new_tokens["must_change_password"] is False

    @pytest.mark.asyncio
    async def test_after_password_change_normal_endpoints_accessible(
        self, client: AsyncClient, must_change_user: User
    ) -> None:
        tokens = await _login(client, "newuser", "temporarypass1")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        await client.post(
            "/api/auth/me/change-password",
            headers=headers,
            json={"current_password": "temporarypass1", "new_password": "newSecurePass8"},
        )

        # Re-login and access normal endpoint
        new_tokens = await _login(client, "newuser", "newSecurePass8")
        new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}

        response = await client.get("/api/auth/me", headers=new_headers)
        assert response.status_code == 200
        assert response.json()["must_change_password"] is False


class TestAdminPasswordResetSetsFlag:
    @pytest.mark.asyncio
    async def test_admin_reset_password_sets_must_change_flag(
        self, client: AsyncClient, admin_user: User, must_change_user: User
    ) -> None:
        # First: clear the flag by changing password normally
        tokens = await _login(client, "newuser", "temporarypass1")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        await client.post(
            "/api/auth/me/change-password",
            headers=headers,
            json={"current_password": "temporarypass1", "new_password": "newSecurePass8"},
        )

        # Admin resets the password
        admin_tokens = await _login(client, "admin", "adminpassword123")
        admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

        response = await client.post(
            f"/api/auth/users/{must_change_user.id}/reset-password",
            headers=admin_headers,
            json={"new_password": "resetPass123"},
        )
        assert response.status_code == 204

        # Verify the flag is set again
        reset_tokens = await _login(client, "newuser", "resetPass123")
        assert reset_tokens["must_change_password"] is True


class TestBootstrapAdminHasMustChangePassword:
    @pytest.mark.asyncio
    async def test_bootstrap_admin_gets_must_change_password_true(
        self, db_session: AsyncSession
    ) -> None:
        """The bootstrap admin created by _bootstrap_admin should have must_change_password=True."""
        # Patch get_session to use our test db_session so _bootstrap_admin
        # writes into the test database instead of the production engine.
        from contextlib import asynccontextmanager
        from unittest.mock import patch

        from backend.database import _bootstrap_admin

        @asynccontextmanager
        async def _fake_get_session():  # type: ignore[no-untyped-def]
            try:
                yield db_session
                await db_session.commit()
            except Exception:
                await db_session.rollback()
                raise

        with patch("backend.database.get_session", _fake_get_session):
            await _bootstrap_admin()

        from sqlalchemy import select

        result = await db_session.execute(select(User).where(User.username == "admin"))
        bootstrap_user = result.scalar_one()
        assert bootstrap_user.must_change_password is True


class TestUserReadIncludesMustChangePassword:
    @pytest.mark.asyncio
    async def test_user_read_exposes_must_change_password(
        self, client: AsyncClient, admin_user: User, must_change_user: User
    ) -> None:
        admin_tokens = await _login(client, "admin", "adminpassword123")
        admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

        response = await client.get("/api/auth/users", headers=admin_headers)
        assert response.status_code == 200
        users = response.json()
        target = next(u for u in users if u["username"] == "newuser")
        assert target["must_change_password"] is True
