"""Accounting accounts service — CRUD and seed."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import (
    DEFAULT_ACCOUNTS,
    AccountingAccount,
    AccountType,
)
from backend.schemas.accounting_account import (
    AccountingAccountCreate,
    AccountingAccountUpdate,
)


async def seed_default_accounts(db: AsyncSession) -> int:
    """Insert the default chart of accounts. Skips already-existing numbers.

    Returns the number of accounts inserted.
    """
    existing_result = await db.execute(select(AccountingAccount.number))
    existing_numbers = {row[0] for row in existing_result.all()}

    inserted = 0
    for data in DEFAULT_ACCOUNTS:
        if data["number"] not in existing_numbers:
            account = AccountingAccount(**data)
            db.add(account)
            inserted += 1
    await db.commit()
    return inserted


async def list_accounts(
    db: AsyncSession,
    *,
    type: AccountType | None = None,
    active_only: bool = True,
) -> list[AccountingAccount]:
    query = select(AccountingAccount)
    if active_only:
        query = query.where(AccountingAccount.is_active == True)  # noqa: E712
    if type is not None:
        query = query.where(AccountingAccount.type == type)
    query = query.order_by(AccountingAccount.number)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_account(db: AsyncSession, account_id: int) -> AccountingAccount | None:
    result = await db.execute(
        select(AccountingAccount).where(AccountingAccount.id == account_id)
    )
    return result.scalar_one_or_none()


async def get_account_by_number(
    db: AsyncSession, number: str
) -> AccountingAccount | None:
    result = await db.execute(
        select(AccountingAccount).where(AccountingAccount.number == number)
    )
    return result.scalar_one_or_none()


async def create_account(
    db: AsyncSession, payload: AccountingAccountCreate
) -> AccountingAccount:
    account = AccountingAccount(**payload.model_dump(), is_default=False)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def update_account(
    db: AsyncSession, account: AccountingAccount, payload: AccountingAccountUpdate
) -> AccountingAccount:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return account
