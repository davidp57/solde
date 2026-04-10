"""Accounting accounts API router — chart of accounts CRUD and seed."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.accounting_account import AccountType
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.accounting_account import (
    AccountingAccountCreate,
    AccountingAccountRead,
    AccountingAccountUpdate,
)
from backend.services import accounting_account as account_service

router = APIRouter(prefix="/accounting/accounts", tags=["accounting"])

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=list[AccountingAccountRead])
async def list_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    type: AccountType | None = Query(default=None),
    active_only: bool = Query(default=True),
) -> list[AccountingAccountRead]:
    """List accounts, optionally filtered by type."""
    accounts = await account_service.list_accounts(
        db, type=type, active_only=active_only
    )
    return accounts  # type: ignore[return-value]


@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> dict[str, int]:
    """Seed the default chart of accounts (idempotent — skips existing numbers)."""
    inserted = await account_service.seed_default_accounts(db)
    return {"inserted": inserted}


@router.post(
    "/", response_model=AccountingAccountRead, status_code=status.HTTP_201_CREATED
)
async def create_account(
    payload: AccountingAccountCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> AccountingAccountRead:
    """Create a new account."""
    existing = await account_service.get_account_by_number(db, payload.number)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account number {payload.number} already exists",
        )
    return await account_service.create_account(db, payload)  # type: ignore[return-value]


@router.get("/{account_id}", response_model=AccountingAccountRead)
async def get_account(
    account_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> AccountingAccountRead:
    account = await account_service.get_account(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return account  # type: ignore[return-value]


@router.put("/{account_id}", response_model=AccountingAccountRead)
async def update_account(
    account_id: int,
    payload: AccountingAccountUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> AccountingAccountRead:
    account = await account_service.get_account(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return await account_service.update_account(db, account, payload)  # type: ignore[return-value]
