"""Bank service — transactions, deposit slips and reconciliation."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank import BankTransaction, Deposit, deposit_payments
from backend.models.payment import Payment
from backend.schemas.bank import BankTransactionCreate, BankTransactionUpdate, DepositCreate


async def _current_bank_balance(db: AsyncSession) -> Decimal:
    """Return the sum of all bank transaction amounts (positive = credit)."""
    result = await db.execute(select(func.sum(BankTransaction.amount)))
    total = result.scalar_one_or_none() or Decimal("0")
    return Decimal(str(total))


async def add_transaction(db: AsyncSession, payload: BankTransactionCreate) -> BankTransaction:
    tx = BankTransaction(**payload.model_dump())
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


async def get_transaction(db: AsyncSession, tx_id: int) -> BankTransaction | None:
    result = await db.execute(select(BankTransaction).where(BankTransaction.id == tx_id))
    return result.scalar_one_or_none()


async def list_transactions(
    db: AsyncSession,
    *,
    unreconciled_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[BankTransaction]:
    query = select(BankTransaction)
    if unreconciled_only:
        query = query.where(BankTransaction.reconciled == False)  # noqa: E712
    query = query.order_by(BankTransaction.date.desc(), BankTransaction.id.desc())
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_transaction(
    db: AsyncSession, tx: BankTransaction, payload: BankTransactionUpdate
) -> BankTransaction:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
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

    total_amount = sum(Decimal(str(p.amount)) for p in payments)

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

    await db.commit()
    await db.refresh(deposit)
    return deposit


async def get_deposit(db: AsyncSession, deposit_id: int) -> Deposit | None:
    result = await db.execute(select(Deposit).where(Deposit.id == deposit_id))
    return result.scalar_one_or_none()


async def list_deposits(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Deposit]:
    result = await db.execute(
        select(Deposit).order_by(Deposit.date.desc(), Deposit.id.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_deposit_payment_ids(db: AsyncSession, deposit_id: int) -> list[int]:
    result = await db.execute(
        select(deposit_payments.c.payment_id).where(deposit_payments.c.deposit_id == deposit_id)
    )
    return [row[0] for row in result.all()]
