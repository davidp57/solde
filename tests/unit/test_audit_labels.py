"""Tests for audit target labels and the audit journal search (lot AUDIT-LOG)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.audit_log import AuditLog
from backend.models.bank import BankTransaction, BankTransactionSource
from backend.models.contact import Contact, ContactType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.services.audit_labels import describe_target, describe_targets
from backend.services.audit_service import (
    AuditAction,
    backfill_target_labels,
    record_audit,
    search_audit_logs,
)


async def _tx(db: AsyncSession, amount: str = "1234.50", description: str = "VIR DUPONT") -> int:
    tx = BankTransaction(
        date=date(2026, 3, 15),
        amount=Decimal(amount),
        description=description,
        balance_after=Decimal("0"),
        source=BankTransactionSource.MANUAL,
    )
    db.add(tx)
    await db.flush()
    return tx.id


async def test_bank_transaction_label_reads_like_the_statement(db_session: AsyncSession):
    tx_id = await _tx(db_session)
    label = await describe_target(db_session, "bank_transaction", tx_id)
    assert label == "15/03/2026 · 1 234,50 € · VIR DUPONT"


async def test_invoice_label_names_number_and_contact(db_session: AsyncSession):
    contact = Contact(type=ContactType.CLIENT, nom="Dupont", prenom="Marie")
    db_session.add(contact)
    await db_session.flush()
    invoice = Invoice(
        number="F-2026-012",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2026, 3, 1),
        total_amount=Decimal("150"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(invoice)
    await db_session.flush()
    assert await describe_target(db_session, "invoice", invoice.id) == "F-2026-012 · Marie Dupont"


async def test_missing_target_and_unknown_type_have_no_label(db_session: AsyncSession):
    labels = await describe_targets(db_session, [("bank_transaction", 999), ("nope", 1)])
    assert labels == {}


async def test_record_audit_snapshots_the_target(db_session: AsyncSession):
    tx_id = await _tx(db_session)
    log = await record_audit(
        db_session,
        action=AuditAction.BANK_PAYMENT_CREATED,
        target_type="bank_transaction",
        target_id=tx_id,
    )
    assert log.target_label == "15/03/2026 · 1 234,50 € · VIR DUPONT"


async def test_backfill_labels_past_entries_once(db_session: AsyncSession):
    tx_id = await _tx(db_session)
    db_session.add_all(
        [
            AuditLog(
                action="bank.transaction.update", target_type="bank_transaction", target_id=tx_id
            ),
            AuditLog(
                action="bank.transaction.delete", target_type="bank_transaction", target_id=999
            ),
            AuditLog(action="auth.logout"),
        ]
    )
    await db_session.flush()

    assert await backfill_target_labels(db_session) == 2
    # The deleted target gets "", so it is not looked up again on the next start.
    assert await backfill_target_labels(db_session) == 0
    logs, _ = await search_audit_logs(db_session, q="VIR DUPONT")
    assert [log.target_id for log in logs] == [tx_id]


async def _seed(db: AsyncSession) -> int:
    tx_id = await _tx(db)
    await record_audit(
        db, action=AuditAction.BANK_PAYMENT_CREATED, target_type="bank_transaction", target_id=tx_id
    )
    await record_audit(db, action=AuditAction.LOGOUT, detail={"ip": "10.0.0.7"})
    await record_audit(db, action=AuditAction.BANK_IMPORTED, detail={"format": "ofx"})
    await db.flush()
    return tx_id


async def test_search_matches_target_label_detail_and_id(db_session: AsyncSession):
    tx_id = await _seed(db_session)

    by_label, total = await search_audit_logs(db_session, q="dupont")
    assert total == 1 and by_label[0].target_id == tx_id

    by_detail, _ = await search_audit_logs(db_session, q="10.0.0.7")
    assert [log.action for log in by_detail] == ["auth.logout"]

    by_id, _ = await search_audit_logs(db_session, q=f"#{tx_id}")
    assert [log.target_id for log in by_id] == [tx_id]


async def test_search_matches_translated_action_names(db_session: AsyncSession):
    """« rapprochement » only exists in the interface: it sends the matching codes."""
    await _seed(db_session)
    logs, _ = await search_audit_logs(
        db_session, q="rapprochement", q_actions=["bank.reconcile.payment"]
    )
    assert [log.action for log in logs] == ["bank.reconcile.payment"]


async def test_action_prefix_and_pagination(db_session: AsyncSession):
    await _seed(db_session)
    page, total = await search_audit_logs(db_session, action_prefix="bank.", limit=1)
    assert total == 2
    assert len(page) == 1
