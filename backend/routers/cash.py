"""Cash register API router — journal entries, balance and cash counts."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.cash import CashEntrySource
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.cash import (
    CashBalanceRead,
    CashCountCreate,
    CashCountRead,
    CashEntryConnectionsRead,
    CashEntryCreate,
    CashEntryRead,
    CashEntryUpdate,
    LinkedAccountingEntry,
)
from backend.services import cash_service

router = APIRouter(prefix="/cash", tags=["cash"])

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]


@router.get("/balance", response_model=CashBalanceRead)
async def get_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> CashBalanceRead:
    balance = await cash_service.get_cash_balance(db)
    return CashBalanceRead(balance=balance)


@router.get("/chart/funds")
async def get_funds_chart(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    months: int = Query(default=6, ge=1, le=24),
) -> list[dict[str, Decimal | str]]:
    return await cash_service.get_monthly_funds_series(db, months=months)


@router.get("/entries", response_model=list[CashEntryRead])
async def list_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=5000, ge=1, le=10000),
) -> list[CashEntryRead]:
    return await cash_service.list_cash_entries(
        db,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )  # type: ignore[return-value]


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


@router.get("/entries/{entry_id}/connections", response_model=CashEntryConnectionsRead)
async def get_entry_connections(
    entry_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> CashEntryConnectionsRead:
    entry = await cash_service.get_cash_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash entry not found")
    if entry.source != CashEntrySource.MANUAL:
        return CashEntryConnectionsRead(
            can_delete=False,
            blocking_reason="non_manual",
        )
    if entry.payment_id is not None:
        return CashEntryConnectionsRead(
            can_delete=False,
            blocking_reason="has_payment",
        )
    acc_entries = await cash_service.get_cash_entry_accounting_entries(db, entry_id)
    return CashEntryConnectionsRead(
        can_delete=True,
        accounting_entries=[LinkedAccountingEntry.model_validate(e) for e in acc_entries],
    )


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


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> None:
    entry = await cash_service.get_cash_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash entry not found")
    if entry.source != CashEntrySource.MANUAL:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only manual cash entries can be deleted",
        )
    try:
        await cash_service.delete_cash_entry(db, entry)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/counts", response_model=list[CashCountRead])
async def list_counts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=5000, ge=1, le=10000),
) -> list[CashCountRead]:
    return await cash_service.list_cash_counts(
        db,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )  # type: ignore[return-value]


@router.post("/counts", response_model=CashCountRead, status_code=status.HTTP_201_CREATED)
async def add_count(
    payload: CashCountCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> CashCountRead:
    return await cash_service.create_cash_count(db, payload)  # type: ignore[return-value]
