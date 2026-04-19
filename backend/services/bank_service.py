"""Bank service — transactions, deposit slips and reconciliation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank import (
    BankTransaction,
    BankTransactionSource,
    Deposit,
    DepositType,
    deposit_payments,
)
from backend.models.cash import CashEntrySource, CashMovementType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.bank import BankTransactionCreate, BankTransactionUpdate, DepositCreate


async def _current_bank_balance(db: AsyncSession) -> Decimal:
    """Return the sum of all bank transaction amounts (positive = credit)."""
    result = await db.execute(select(func.sum(BankTransaction.amount)))
    total = result.scalar_one_or_none() or Decimal("0")
    return Decimal(str(total))


async def recompute_bank_balances(db: AsyncSession) -> bool:
    """Recompute running bank balances and report whether persisted values changed."""
    result = await db.execute(
        select(BankTransaction).order_by(BankTransaction.date.asc(), BankTransaction.id.asc())
    )
    running_balance = Decimal("0")
    changed = False
    for entry in result.scalars().all():
        running_balance += Decimal(str(entry.amount))
        if entry.balance_after != running_balance:
            entry.balance_after = running_balance
            changed = True
    return changed


async def add_transaction(db: AsyncSession, payload: BankTransactionCreate) -> BankTransaction:
    tx = await create_bank_transaction_record(
        db,
        date=payload.date,
        amount=payload.amount,
        reference=payload.reference,
        description=payload.description,
        source=payload.source,
    )
    await db.commit()
    await db.refresh(tx)
    return tx


async def create_bank_transaction_record(
    db: AsyncSession,
    *,
    date: date,
    amount: Decimal,
    reference: str | None = None,
    description: str = "",
    source: BankTransactionSource = BankTransactionSource.MANUAL,
) -> BankTransaction:
    """Create a bank transaction without committing, then recompute balances."""
    tx = BankTransaction(
        date=date,
        amount=amount,
        reference=reference,
        description=description,
        balance_after=Decimal("0"),
        source=source,
    )
    db.add(tx)
    await db.flush()
    await recompute_bank_balances(db)
    return tx


async def get_transaction(db: AsyncSession, tx_id: int) -> BankTransaction | None:
    result = await db.execute(select(BankTransaction).where(BankTransaction.id == tx_id))
    return result.scalar_one_or_none()


async def list_transactions(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    unreconciled_only: bool = False,
    skip: int = 0,
    limit: int | None = None,
) -> list[BankTransaction]:
    query = select(BankTransaction)
    if from_date is not None:
        query = query.where(BankTransaction.date >= from_date)
    if to_date is not None:
        query = query.where(BankTransaction.date <= to_date)
    if unreconciled_only:
        query = query.where(BankTransaction.reconciled == False)  # noqa: E712
    query = query.order_by(BankTransaction.date.desc(), BankTransaction.id.desc())
    query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_transaction(
    db: AsyncSession, tx: BankTransaction, payload: BankTransactionUpdate
) -> BankTransaction:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
    await db.flush()
    await recompute_bank_balances(db)
    await db.commit()
    await db.refresh(tx)
    return tx


async def get_bank_balance(db: AsyncSession) -> Decimal:
    return await _current_bank_balance(db)


# ---------------------------------------------------------------------------
# Deposit slips
# ---------------------------------------------------------------------------


async def create_deposit(db: AsyncSession, payload: DepositCreate) -> Deposit:
    """Create a deposit slip and mark its payments as deposited."""
    # Load payments and verify they exist
    result = await db.execute(select(Payment).where(Payment.id.in_(payload.payment_ids)))
    payments = list(result.scalars().all())
    if len(payments) != len(payload.payment_ids):
        raise ValueError("one or more payment_ids not found")

    expected_method = (
        PaymentMethod.CHEQUE if payload.type == DepositType.CHEQUES else PaymentMethod.ESPECES
    )
    invalid_payment = next(
        (payment for payment in payments if payment.method != expected_method),
        None,
    )
    if invalid_payment is not None:
        raise ValueError("deposit payments must match the selected deposit type")

    total_amount = sum((Decimal(str(payment.amount)) for payment in payments), Decimal("0"))

    deposit = Deposit(
        date=payload.date,
        type=payload.type,
        total_amount=total_amount,
        bank_reference=payload.bank_reference,
        notes=payload.notes,
    )
    db.add(deposit)
    await db.flush()

    # Create association rows
    await db.execute(
        insert(deposit_payments),
        [{"deposit_id": deposit.id, "payment_id": pid} for pid in payload.payment_ids],
    )

    # Mark payments as deposited
    for p in payments:
        p.deposited = True
        p.deposit_date = payload.date

    if payload.type == DepositType.ESPECES:
        from backend.services.cash_service import create_cash_entry_record  # noqa: PLC0415

        reference = payload.bank_reference or f"DEP-ESP-{deposit.id}"
        await create_cash_entry_record(
            db,
            date=payload.date,
            amount=total_amount,
            type=CashMovementType.OUT,
            reference=reference,
            description="Remise d'especes en banque",
            source=CashEntrySource.DEPOSIT,
        )

    # Auto-generate accounting entries
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_deposit,
    )

    await generate_entries_for_deposit(db, deposit)

    await db.commit()
    await db.refresh(deposit)
    return deposit


async def get_deposit(db: AsyncSession, deposit_id: int) -> Deposit | None:
    result = await db.execute(select(Deposit).where(Deposit.id == deposit_id))
    return result.scalar_one_or_none()


async def list_deposits(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    skip: int = 0,
    limit: int | None = None,
) -> list[Deposit]:
    query = select(Deposit)
    if from_date is not None:
        query = query.where(Deposit.date >= from_date)
    if to_date is not None:
        query = query.where(Deposit.date <= to_date)
    query = query.order_by(Deposit.date.desc(), Deposit.id.desc()).offset(skip)
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_deposit_payment_ids(db: AsyncSession, deposit_id: int) -> list[int]:
    result = await db.execute(
        select(deposit_payments.c.payment_id).where(deposit_payments.c.deposit_id == deposit_id)
    )
    return [row[0] for row in result.all()]
