"""Bank deposits sub-router — deposit slips CRUD."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import api_error, not_found, unprocessable
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.bank import (
    DepositCreate,
    DepositRead,
    DepositUpdate,
)
from backend.services import bank_service
from backend.services.audit_service import AuditAction, record_audit

router = APIRouter()

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]


# ---------------------------------------------------------------------------
# Deposit slips
# ---------------------------------------------------------------------------


@router.get("/deposits", response_model=list[DepositRead])
async def list_deposits(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    confirmed: bool | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=1000, ge=1, le=5000),
) -> list[DepositRead]:
    deposits = await bank_service.list_deposits(
        db,
        from_date=from_date,
        to_date=to_date,
        confirmed=confirmed,
        skip=skip,
        limit=limit,
    )
    total = await bank_service.count_deposits(
        db,
        from_date=from_date,
        to_date=to_date,
        confirmed=confirmed,
    )
    response.headers["X-Total-Count"] = str(total)
    result: list[DepositRead] = []
    for d in deposits:
        pids = await bank_service.get_deposit_payment_ids(db, d.id)
        result.append(
            DepositRead(
                id=d.id,
                date=d.date,
                type=d.type,
                total_amount=d.total_amount,
                bank_reference=d.bank_reference,
                notes=d.notes,
                denomination_details=d.denomination_details,
                confirmed=d.confirmed,
                confirmed_date=d.confirmed_date,
                payment_ids=pids,
            )
        )
    return result


@router.post("/deposits", response_model=DepositRead, status_code=status.HTTP_201_CREATED)
async def create_deposit(
    payload: DepositCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> DepositRead:
    try:
        deposit = await bank_service.create_deposit(db, payload)
    except ValueError as exc:
        raise unprocessable("BANK_DEPOSIT_INVALID", str(exc)) from exc
    pids = await bank_service.get_deposit_payment_ids(db, deposit.id)
    await record_audit(
        db,
        action=AuditAction.BANK_DEPOSIT_CREATED,
        actor=current_user,
        target_id=deposit.id,
        target_type="bank_deposit",
        detail={
            "date": str(deposit.date),
            "total_amount": str(deposit.total_amount),
            "payment_count": len(pids),
        },
    )
    return DepositRead(
        id=deposit.id,
        date=deposit.date,
        type=deposit.type,
        total_amount=deposit.total_amount,
        bank_reference=deposit.bank_reference,
        notes=deposit.notes,
        denomination_details=deposit.denomination_details,
        confirmed=deposit.confirmed,
        confirmed_date=deposit.confirmed_date,
        payment_ids=pids,
    )


@router.post("/deposits/{deposit_id}/confirm", response_model=DepositRead)
async def confirm_deposit(
    deposit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> DepositRead:
    try:
        deposit = await bank_service.confirm_deposit(db, deposit_id)
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "DEPOSIT_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_DEPOSIT_INVALID", str(exc)) from exc
    pids = await bank_service.get_deposit_payment_ids(db, deposit.id)
    await record_audit(
        db,
        action=AuditAction.BANK_DEPOSIT_CONFIRMED,
        actor=current_user,
        target_id=deposit.id,
        target_type="bank_deposit",
        detail={"confirmed_date": str(deposit.confirmed_date)},
    )
    return DepositRead(
        id=deposit.id,
        date=deposit.date,
        type=deposit.type,
        total_amount=deposit.total_amount,
        bank_reference=deposit.bank_reference,
        notes=deposit.notes,
        denomination_details=deposit.denomination_details,
        confirmed=deposit.confirmed,
        confirmed_date=deposit.confirmed_date,
        payment_ids=pids,
    )


@router.get("/deposits/{deposit_id}", response_model=DepositRead)
async def get_deposit(
    deposit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> DepositRead:
    deposit = await bank_service.get_deposit(db, deposit_id)
    if deposit is None:
        raise not_found("Deposit")
    pids = await bank_service.get_deposit_payment_ids(db, deposit_id)
    return DepositRead(
        id=deposit.id,
        date=deposit.date,
        type=deposit.type,
        total_amount=deposit.total_amount,
        bank_reference=deposit.bank_reference,
        notes=deposit.notes,
        denomination_details=deposit.denomination_details,
        confirmed=deposit.confirmed,
        confirmed_date=deposit.confirmed_date,
        payment_ids=pids,
    )


@router.patch("/deposits/{deposit_id}", response_model=DepositRead)
async def update_deposit(
    deposit_id: int,
    payload: DepositUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> DepositRead:
    try:
        deposit = await bank_service.update_deposit(db, deposit_id, payload)
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "DEPOSIT_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_DEPOSIT_INVALID", str(exc)) from exc
    pids = await bank_service.get_deposit_payment_ids(db, deposit.id)
    await record_audit(
        db,
        action=AuditAction.BANK_DEPOSIT_UPDATED,
        actor=current_user,
        target_id=deposit.id,
        target_type="bank_deposit",
        detail={
            "action": "updated",
            "total_amount": str(deposit.total_amount),
            "payment_count": len(pids),
        },
    )
    return DepositRead(
        id=deposit.id,
        date=deposit.date,
        type=deposit.type,
        total_amount=deposit.total_amount,
        bank_reference=deposit.bank_reference,
        notes=deposit.notes,
        denomination_details=deposit.denomination_details,
        confirmed=deposit.confirmed,
        confirmed_date=deposit.confirmed_date,
        payment_ids=pids,
    )


@router.delete("/deposits/{deposit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deposit(
    deposit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> None:
    try:
        await bank_service.delete_deposit(db, deposit_id)
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "DEPOSIT_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_DEPOSIT_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_DEPOSIT_CANCELLED,
        actor=current_user,
        target_id=deposit_id,
        target_type="bank_deposit",
        detail={"action": "cancelled"},
    )
