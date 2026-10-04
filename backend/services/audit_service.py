"""Audit service — record security-sensitive actions."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import ColumnElement, String, cast, func, or_, select

from backend.models.audit_log import AuditLog
from backend.services.audit_labels import describe_target, describe_targets

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
    SETTINGS_UPDATED = "admin.settings.update"
    BACKUP_RESTORED = "admin.backup.restore"
    BACKUP_DESTINATION_CREATED = "admin.backup.destination.create"
    BACKUP_DESTINATION_UPDATED = "admin.backup.destination.update"
    BACKUP_DESTINATION_DELETED = "admin.backup.destination.delete"
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
    INVOICE_ENTRIES_REGENERATED = "invoice.entries.regenerate"
    INVOICE_BULK_ARCHIVED = "invoice.bulk_archive"
    # Documents
    DOCUMENT_UPLOADED = "document.upload"
    DOCUMENT_UPDATED = "document.update"
    DOCUMENT_DELETED = "document.delete"
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
    BANK_TRANSACTION_DELETED = "bank.transaction.delete"
    BANK_TRANSACTION_BULK_RECONCILED = "bank.transaction.bulk_reconcile"
    BANK_TRANSACTION_UNRECONCILED = "bank.transaction.unreconcile"
    BANK_PAYMENT_CREATED = "bank.reconcile.payment"
    BANK_IMPORTED = "bank.import"
    BANK_DEPOSIT_CREATED = "bank.deposit.create"
    BANK_DEPOSIT_UPDATED = "bank.deposit.update"
    BANK_DEPOSIT_CANCELLED = "bank.deposit.cancel"
    BANK_DEPOSIT_CONFIRMED = "bank.deposit.confirm"
    BANK_DEPOSIT_MERGED = "bank.deposit.merge"
    CHECKLIST_SESSION_OPENED = "checklist.session.open"
    CHECKLIST_SESSION_CLOSED = "checklist.session.close"
    # Contacts
    CONTACT_CREATED = "contact.create"
    CONTACT_UPDATED = "contact.update"
    CONTACT_DELETED = "contact.delete"
    CONTACT_CREANCE_DOUTEUSE = "contact.creance_douteuse"
    CONTACT_MERGED = "contact.merge"
    MEMBER_MAILING_SENT = "contact.mailing.send"
    # Excel import
    IMPORT_EXECUTED = "import.run.execute"
    IMPORT_UNDONE = "import.run.undo"
    IMPORT_REDONE = "import.run.redo"
    # Chat / AI assistant
    CHAT_QUERIED = "chat.query"


async def record_audit(
    db: AsyncSession,
    *,
    action: AuditAction,
    actor: User | None = None,
    target_id: int | None = None,
    target_type: str | None = None,
    detail: dict[str, Any] | None = None,
    target_label: str | None = None,
) -> AuditLog:
    """Insert an audit log entry in the current transaction.

    The target's label is looked up here; a caller about to delete the target must
    read it first (:func:`describe_target`) and pass it as *target_label*.
    """
    if target_label is None and target_type is not None and target_id is not None:
        target_label = await describe_target(db, target_type, target_id)
    log = AuditLog(
        action=action,
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else None,
        target_id=target_id,
        target_type=target_type,
        target_label=target_label,
        detail=detail,
    )
    db.add(log)
    return log


#: Rows labelled per batch by :func:`backfill_target_labels`.
_BACKFILL_BATCH = 500


async def backfill_target_labels(db: AsyncSession) -> int:
    """Label the entries recorded before ``target_label`` existed. Returns the count.

    Runs at startup and is a no-op once done: a target that no longer exists gets an
    empty label, so it is not looked up again.
    """
    labelled = 0
    while True:
        rows = await db.execute(
            select(AuditLog)
            .where(AuditLog.target_label.is_(None))
            .where(AuditLog.target_type.is_not(None))
            .where(AuditLog.target_id.is_not(None))
            .limit(_BACKFILL_BATCH)
        )
        logs = list(rows.scalars())
        if not logs:
            return labelled
        targets = [
            (log.target_type, log.target_id) for log in logs if log.target_type and log.target_id
        ]
        labels = await describe_targets(db, targets)
        for log in logs:
            log.target_label = labels.get((log.target_type or "", log.target_id or 0), "")
        await db.flush()
        labelled += len(logs)


async def search_audit_logs(
    db: AsyncSession,
    *,
    q: str | None = None,
    q_actions: Sequence[str] = (),
    action_prefix: str | None = None,
    actor_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[AuditLog], int]:
    """Return one page of audit entries, newest first, and the total matching count.

    *q* matches the actor, the target label, the target type, the action code and the
    detail. Action names are translated in the interface only, so the caller also
    passes in *q_actions* the codes whose displayed name matches *q*. A ``#123`` query
    matches the target id.
    """
    stmt = select(AuditLog)
    if q and q.strip():
        term = q.strip()
        pattern = f"%{term}%"
        conditions: list[ColumnElement[bool]] = [
            AuditLog.actor_username.ilike(pattern),
            AuditLog.target_label.ilike(pattern),
            AuditLog.target_type.ilike(pattern),
            AuditLog.action.ilike(pattern),
            cast(AuditLog.detail, String).ilike(pattern),
        ]
        if q_actions:
            conditions.append(AuditLog.action.in_(list(q_actions)))
        if term.lstrip("#").isdigit():
            conditions.append(AuditLog.target_id == int(term.lstrip("#")))
        stmt = stmt.where(or_(*conditions))
    if action_prefix:
        stmt = stmt.where(AuditLog.action.startswith(action_prefix, autoescape=True))
    if actor_id is not None:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if from_date is not None:
        stmt = stmt.where(AuditLog.created_at >= _as_utc(from_date))
    if to_date is not None:
        stmt = stmt.where(AuditLog.created_at <= _as_utc(to_date))

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    page = await db.execute(
        stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(skip).limit(limit)
    )
    return list(page.scalars()), int(total)


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
