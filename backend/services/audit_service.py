"""Audit service — record security-sensitive actions."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from backend.models.audit_log import AuditLog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from backend.models.user import User


class AuditAction(StrEnum):
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGED = "auth.password.change"
    USER_CREATED = "admin.user.create"
    USER_UPDATED = "admin.user.update"
    PASSWORD_RESET_BY_ADMIN = "admin.user.password_reset"
    DB_RESET = "admin.reset_db"
    SELECTIVE_RESET = "admin.selective_reset"


async def record_audit(
    db: AsyncSession,
    *,
    action: AuditAction,
    actor: User | None = None,
    target_id: int | None = None,
    target_type: str | None = None,
    detail: dict[str, Any] | None = None,
) -> AuditLog:
    """Insert an audit log entry in the current transaction."""
    log = AuditLog(
        action=action,
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else None,
        target_id=target_id,
        target_type=target_type,
        detail=detail,
    )
    db.add(log)
    return log
