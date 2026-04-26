"""Payments API router — CRUD and deposit filtering."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.invoice import InvoiceType
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from backend.services import payment as payment_service
from backend.services.audit_service import AuditAction, record_audit

router = APIRouter(prefix="/payments", tags=["payments"])

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]


@router.get("/", response_model=list[PaymentRead])
async def list_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    invoice_id: int | None = Query(default=None),
    invoice_type: InvoiceType | None = Query(default=None),
    contact_id: int | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    undeposited_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[PaymentRead]:
    payments = await payment_service.list_payments(
        db,
        invoice_id=invoice_id,
        invoice_type=invoice_type,
        contact_id=contact_id,
        from_date=from_date,
        to_date=to_date,
        undeposited_only=undeposited_only,
        skip=skip,
        limit=limit,
    )
    return payments


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> PaymentRead:
    try:
        payment = await payment_service.create_payment(db, payload)
    except payment_service.InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.PAYMENT_CREATED,
        actor=current_user,
        target_id=payment.id,
        target_type="payment",
        detail={
            "invoice_id": payment.invoice_id,
            "amount": str(payment.amount),
            "method": payment.method,
        },
    )
    return payment


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> PaymentRead:
    payment = await payment_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.put("/{payment_id}", response_model=PaymentRead)
async def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> PaymentRead:
    try:
        updated = await payment_service.update_payment(db, payment_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.PAYMENT_UPDATED,
        actor=current_user,
        target_id=payment_id,
        target_type="payment",
    )
    return updated


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> None:
    payment = await payment_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    detail = {
        "invoice_id": payment.invoice_id,
        "amount": str(payment.amount),
        "method": payment.method,
    }
    try:
        await payment_service.delete_payment(db, payment_id)
    except payment_service.PaymentDeleteError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.PAYMENT_DELETED,
        actor=current_user,
        target_id=payment_id,
        target_type="payment",
        detail=detail,
    )
