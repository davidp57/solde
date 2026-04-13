"""Cash register API router — journal entries, balance and cash counts."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.cash import (
    CashBalanceRead,
    CashCountCreate,
    CashCountRead,
    CashEntryCreate,
    CashEntryRead,
    CashEntryUpdate,
)
from backend.services import cash_service

router = APIRouter(prefix="/cash", tags=["cash"])

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[User, Depends(get_current_user)]


@router.get("/balance", response_model=CashBalanceRead)
async def get_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> CashBalanceRead:
    balance = await cash_service.get_cash_balance(db)
    return CashBalanceRead(balance=balance)


@router.get("/entries", response_model=list[CashEntryRead])
async def list_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[CashEntryRead]:
    return await cash_service.list_cash_entries(db, skip=skip, limit=limit)  # type: ignore[return-value]


@router.post("/entries", response_model=CashEntryRead, status_code=status.HTTP_201_CREATED)
async def add_entry(
    payload: CashEntryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> CashEntryRead:
    return await cash_service.add_cash_entry(db, payload)  # type: ignore[return-value]


@router.get("/entries/{entry_id}", response_model=CashEntryRead)
async def get_entry(
    entry_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> CashEntryRead:
    entry = await cash_service.get_cash_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash entry not found")
    return entry  # type: ignore[return-value]


@router.put("/entries/{entry_id}", response_model=CashEntryRead)
async def update_entry(
    entry_id: int,
    payload: CashEntryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> CashEntryRead:
    entry = await cash_service.get_cash_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash entry not found")
    return await cash_service.update_cash_entry(db, entry, payload)  # type: ignore[return-value]


@router.get("/counts", response_model=list[CashCountRead])
async def list_counts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[CashCountRead]:
    return await cash_service.list_cash_counts(db, skip=skip, limit=limit)  # type: ignore[return-value]


@router.post("/counts", response_model=CashCountRead, status_code=status.HTTP_201_CREATED)
async def add_count(
    payload: CashCountCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> CashCountRead:
    return await cash_service.create_cash_count(db, payload)  # type: ignore[return-value]
