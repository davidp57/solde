"""Unit tests for the bank service — transactions, deposits, balance."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank import BankTransactionSource, DepositType
from backend.models.contact import Contact, ContactType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.bank import (
    BankTransactionCreate,
    BankTransactionUpdate,
    DepositCreate,
)
from backend.services import bank_service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_payment(db: AsyncSession) -> Payment:
    contact = Contact(type=ContactType.CLIENT, nom="Martin")
    db.add(contact)
    await db.flush()

    inv = Invoice(
        number="F-2024-001",
        type=InvoiceType.CLIENT,
        contact_id=contact.id,
        date=date(2024, 1, 15),
        total_amount=Decimal("100.00"),
        paid_amount=Decimal("0"),
        status=InvoiceStatus.SENT,
    )
    db.add(inv)
    await db.flush()

    payment = Payment(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("100.00"),
        date=date(2024, 2, 1),
        method=PaymentMethod.CHEQUE,
        deposited=False,
    )
    db.add(payment)
    await db.flush()
    return payment


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_transaction(db_session: AsyncSession) -> None:
    payload = BankTransactionCreate(
        date=date(2024, 3, 1),
        amount=Decimal("500.00"),
        description="Virement reçu",
        balance_after=Decimal("1500.00"),
    )
    tx = await bank_service.add_transaction(db_session, payload)

    assert tx.id is not None
    assert tx.amount == Decimal("500.00")
    assert tx.reconciled is False
    assert tx.source == BankTransactionSource.MANUAL


@pytest.mark.asyncio
async def test_get_transaction_not_found(db_session: AsyncSession) -> None:
    result = await bank_service.get_transaction(db_session, 9999)
    assert result is None


@pytest.mark.asyncio
async def test_list_transactions(db_session: AsyncSession) -> None:
    for i in range(3):
        await bank_service.add_transaction(
            db_session,
            BankTransactionCreate(
                date=date(2024, 1, i + 1),
                amount=Decimal("100.00"),
            ),
        )
    txs = await bank_service.list_transactions(db_session)
    assert len(txs) == 3


@pytest.mark.asyncio
async def test_list_transactions_unreconciled_only(db_session: AsyncSession) -> None:
    t1 = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 1), amount=Decimal("100.00")),
    )
    await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 2), amount=Decimal("200.00")),
    )
    # manually reconcile t1
    t1.reconciled = True
    await db_session.commit()

    unreconciled = await bank_service.list_transactions(
        db_session, unreconciled_only=True
    )
    assert all(not t.reconciled for t in unreconciled)
    assert len(unreconciled) == 1


@pytest.mark.asyncio
async def test_update_transaction_reconcile(db_session: AsyncSession) -> None:
    tx = await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 1), amount=Decimal("100.00")),
    )
    updated = await bank_service.update_transaction(
        db_session, tx, BankTransactionUpdate(reconciled=True, reconciled_with="REF123")
    )
    assert updated.reconciled is True
    assert updated.reconciled_with == "REF123"


@pytest.mark.asyncio
async def test_get_bank_balance(db_session: AsyncSession) -> None:
    await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 1), amount=Decimal("500.00")),
    )
    await bank_service.add_transaction(
        db_session,
        BankTransactionCreate(date=date(2024, 1, 2), amount=Decimal("-100.00")),
    )
    balance = await bank_service.get_bank_balance(db_session)
    assert balance == Decimal("400.00")


# ---------------------------------------------------------------------------
# Deposits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_deposit_marks_payments_deposited(
    db_session: AsyncSession,
) -> None:
    p = await _make_payment(db_session)
    payload = DepositCreate(
        date=date(2024, 3, 1),
        type=DepositType.CHEQUES,
        payment_ids=[p.id],
        bank_reference="BDX-001",
    )
    deposit = await bank_service.create_deposit(db_session, payload)

    assert deposit.id is not None
    assert deposit.total_amount == Decimal("100.00")

    await db_session.refresh(p)
    assert p.deposited is True
    assert p.deposit_date == date(2024, 3, 1)


@pytest.mark.asyncio
async def test_create_deposit_invalid_payment_raises(db_session: AsyncSession) -> None:
    payload = DepositCreate(
        date=date(2024, 3, 1),
        type=DepositType.CHEQUES,
        payment_ids=[99999],
    )
    with pytest.raises(ValueError, match="not found"):
        await bank_service.create_deposit(db_session, payload)


@pytest.mark.asyncio
async def test_get_deposit_payment_ids(db_session: AsyncSession) -> None:
    p = await _make_payment(db_session)
    deposit = await bank_service.create_deposit(
        db_session,
        DepositCreate(
            date=date(2024, 3, 1),
            type=DepositType.CHEQUES,
            payment_ids=[p.id],
        ),
    )
    ids = await bank_service.get_deposit_payment_ids(db_session, deposit.id)
    assert ids == [p.id]


@pytest.mark.asyncio
async def test_list_deposits(db_session: AsyncSession) -> None:
    p1 = await _make_payment(db_session)

    contact = await db_session.get(Contact, p1.contact_id)
    assert contact is not None
    inv = await db_session.get(Invoice, p1.invoice_id)
    assert inv is not None
    p2 = Payment(
        invoice_id=inv.id,
        contact_id=contact.id,
        amount=Decimal("50.00"),
        date=date(2024, 2, 2),
        method=PaymentMethod.CHEQUE,
        deposited=False,
    )
    db_session.add(p2)
    await db_session.flush()

    await bank_service.create_deposit(
        db_session,
        DepositCreate(
            date=date(2024, 3, 1), type=DepositType.CHEQUES, payment_ids=[p1.id]
        ),
    )
    await bank_service.create_deposit(
        db_session,
        DepositCreate(
            date=date(2024, 3, 2), type=DepositType.ESPECES, payment_ids=[p2.id]
        ),
    )

    deposits = await bank_service.list_deposits(db_session)
    assert len(deposits) == 2
