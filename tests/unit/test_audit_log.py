"""Tests for the structured audit log service (BL-056)."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.audit_log import AuditLog
from backend.models.user import User
from backend.services.audit_service import AuditAction, record_audit


class TestAuditModel:
    """Verify the AuditLog ORM model."""

    @pytest.mark.asyncio
    async def test_audit_log_persists(self, db_session: AsyncSession) -> None:
        log = AuditLog(
            action="auth.login.success",
            actor_id=1,
            actor_username="admin",
            detail={"ip": "127.0.0.1"},
        )
        db_session.add(log)
        await db_session.flush()
        assert log.id is not None
        assert log.created_at is not None

    @pytest.mark.asyncio
    async def test_audit_log_nullable_actor(self, db_session: AsyncSession) -> None:
        """Failed login has no authenticated actor."""
        log = AuditLog(
            action="auth.login.failure",
            actor_id=None,
            actor_username=None,
            detail={"attempted_username": "ghost", "ip": "10.0.0.1"},
        )
        db_session.add(log)
        await db_session.flush()
        assert log.id is not None


class TestAuditAction:
    """Verify the AuditAction enum values."""

    def test_login_actions_exist(self) -> None:
        assert AuditAction.LOGIN_SUCCESS == "auth.login.success"
        assert AuditAction.LOGIN_FAILURE == "auth.login.failure"

    def test_admin_actions_exist(self) -> None:
        assert AuditAction.USER_CREATED == "admin.user.create"
        assert AuditAction.USER_UPDATED == "admin.user.update"
        assert AuditAction.PASSWORD_RESET_BY_ADMIN == "admin.user.password_reset"
        assert AuditAction.DB_RESET == "admin.reset_db"

    def test_user_actions_exist(self) -> None:
        assert AuditAction.PASSWORD_CHANGED == "auth.password.change"
        assert AuditAction.LOGOUT == "auth.logout"


class TestRecordAudit:
    """Verify the record_audit helper."""

    @pytest.mark.asyncio
    async def test_record_audit_with_user(self, db_session: AsyncSession, admin_user: User) -> None:
        await record_audit(
            db_session,
            action=AuditAction.LOGIN_SUCCESS,
            actor=admin_user,
            detail={"ip": "192.168.1.1"},
        )
        await db_session.flush()
        result = await db_session.execute(select(AuditLog))
        log = result.scalar_one()
        assert log.action == "auth.login.success"
        assert log.actor_id == admin_user.id
        assert log.actor_username == "admin"
        assert log.detail is not None
        assert log.detail["ip"] == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_record_audit_without_user(self, db_session: AsyncSession) -> None:
        await record_audit(
            db_session,
            action=AuditAction.LOGIN_FAILURE,
            detail={"attempted_username": "nobody", "ip": "10.0.0.5"},
        )
        await db_session.flush()
        result = await db_session.execute(select(AuditLog))
        log = result.scalar_one()
        assert log.actor_id is None
        assert log.actor_username is None
        assert log.detail is not None
        assert log.detail["attempted_username"] == "nobody"

    @pytest.mark.asyncio
    async def test_record_audit_with_target(
        self, db_session: AsyncSession, admin_user: User
    ) -> None:
        await record_audit(
            db_session,
            action=AuditAction.PASSWORD_RESET_BY_ADMIN,
            actor=admin_user,
            target_id=42,
            target_type="user",
            detail={"target_username": "alice"},
        )
        await db_session.flush()
        result = await db_session.execute(select(AuditLog))
        log = result.scalar_one()
        assert log.target_id == 42
        assert log.target_type == "user"
