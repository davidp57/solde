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
    BACKUP_RESTORED = "admin.backup.restore"
    # Payments
    PAYMENT_CREATED = "payment.create"
    PAYMENT_UPDATED = "payment.update"
    PAYMENT_DELETED = "payment.delete"
    # Invoices
    INVOICE_CREATED = "invoice.create"
    INVOICE_UPDATED = "invoice.update"
    INVOICE_STATUS_CHANGED = "invoice.status.change"
    INVOICE_DUPLICATED = "invoice.duplicate"
    INVOICE_DELETED = "invoice.delete"
    INVOICE_EMAIL_SENT = "invoice.email.send"
    INVOICE_WRITTEN_OFF = "invoice.write_off"
    INVOICE_RESTORED_FROM_WRITEOFF = "invoice.restore_from_writeoff"
    # Cash
    CASH_ENTRY_CREATED = "cash.entry.create"
    CASH_ENTRY_UPDATED = "cash.entry.update"
    CASH_ENTRY_DELETED = "cash.entry.delete"
    CASH_COUNT_CREATED = "cash.count.create"
    # Salaries
    SALARY_CREATED = "salary.create"
    SALARY_UPDATED = "salary.update"
    SALARY_DELETED = "salary.delete"
    # Bank
    BANK_TRANSACTION_CREATED = "bank.transaction.create"
    BANK_TRANSACTION_UPDATED = "bank.transaction.update"
    BANK_PAYMENT_CREATED = "bank.reconcile.payment"
    BANK_IMPORTED = "bank.import"
    BANK_DEPOSIT_CREATED = "bank.deposit.create"
    # Contacts
    CONTACT_CREATED = "contact.create"
    CONTACT_UPDATED = "contact.update"
    CONTACT_DELETED = "contact.delete"
    CONTACT_CREANCE_DOUTEUSE = "contact.creance_douteuse"
    # Excel import
    IMPORT_EXECUTED = "import.run.execute"
    IMPORT_UNDONE = "import.run.undo"
    IMPORT_REDONE = "import.run.redo"


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
