"""Integration tests — audit log entries emitted by auth endpoints (BL-056)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.audit_log import AuditLog
from backend.models.user import User


class TestLoginAudit:
    """Login success/failure must create audit entries."""

    @pytest.mark.asyncio
    async def test_successful_login_creates_audit(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ) -> None:
        resp = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpassword123"},
        )
        assert resp.status_code == 200

        await db_session.flush()
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "auth.login.success")
        )
        log = result.scalar_one()
        assert log.actor_id == admin_user.id
        assert log.actor_username == "admin"

    @pytest.mark.asyncio
    async def test_failed_login_creates_audit(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ) -> None:
        resp = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "auth.login.failure")
        )
        log = result.scalar_one()
        assert log.actor_id is None
        assert log.detail is not None
        assert log.detail["attempted_username"] == "admin"

    @pytest.mark.asyncio
    async def test_failed_login_unknown_user_creates_audit(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        resp = await client.post(
            "/api/auth/login",
            data={"username": "ghost", "password": "whatever"},
        )
        assert resp.status_code == 401

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "auth.login.failure")
        )
        log = result.scalar_one()
        assert log.detail is not None
        assert log.detail["attempted_username"] == "ghost"


class TestPasswordChangeAudit:
    """Password change must create audit entry."""

    @pytest.mark.asyncio
    async def test_password_change_creates_audit(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ) -> None:
        # Login first
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpassword123"},
        )
        token = login_resp.json()["access_token"]

        resp = await client.post(
            "/api/auth/me/change-password",
            json={
                "current_password": "adminpassword123",
                "new_password": "newSecurePassword456",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "auth.password.change")
        )
        log = result.scalar_one()
        assert log.actor_id == admin_user.id


class TestAdminUserManagementAudit:
    """Admin user CRUD operations must create audit entries."""

    @pytest.mark.asyncio
    async def test_create_user_creates_audit(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ) -> None:
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpassword123"},
        )
        token = login_resp.json()["access_token"]

        resp = await client.post(
            "/api/auth/users",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "password123",
                "role": "readonly",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "admin.user.create")
        )
        log = result.scalar_one()
        assert log.actor_id == admin_user.id
        assert log.target_type == "user"
        assert log.detail is not None
        assert log.detail["target_username"] == "newuser"

    @pytest.mark.asyncio
    async def test_password_reset_by_admin_creates_audit(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ) -> None:
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpassword123"},
        )
        token = login_resp.json()["access_token"]

        # Create target user first
        create_resp = await client.post(
            "/api/auth/users",
            json={
                "username": "target",
                "email": "target@test.com",
                "password": "password123",
                "role": "readonly",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        target_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/auth/users/{target_id}/reset-password",
            json={"new_password": "resetPassword789"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "admin.user.password_reset")
        )
        log = result.scalar_one()
        assert log.target_id == target_id
        assert log.target_type == "user"
