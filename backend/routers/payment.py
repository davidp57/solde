"""Payments API router — CRUD and deposit filtering."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import api_error, conflict, not_found
from backend.models.invoice import InvoiceType
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from backend.services import payment as payment_service
from backend.services import settings as settings_service
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
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    invoice_id: int | None = Query(default=None),
    invoice_type: InvoiceType | None = Query(default=None),
    contact_id: int | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    undeposited_only: bool = Query(default=False),
    inconsistent_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=1000, ge=1, le=5000),
) -> list[PaymentRead]:
    payments = await payment_service.list_payments(
        db,
        invoice_id=invoice_id,
        invoice_type=invoice_type,
        contact_id=contact_id,
        from_date=from_date,
        to_date=to_date,
        undeposited_only=undeposited_only,
        inconsistent_only=inconsistent_only,
        skip=skip,
        limit=limit,
    )
    total = await payment_service.count_payments(
        db,
        invoice_id=invoice_id,
        invoice_type=invoice_type,
        contact_id=contact_id,
        from_date=from_date,
        to_date=to_date,
        undeposited_only=undeposited_only,
        inconsistent_only=inconsistent_only,
    )
    response.headers["X-Total-Count"] = str(total)
    return payments


@router.get("/suggest_cheque_number", response_model=str)
async def suggest_cheque_number(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    payment_date: date | None = Query(
        default=None, description="Date du paiement (défaut: aujourd'hui)"
    ),
) -> str:
    """Return the next suggested cheque number for a given date."""
    effective_date = payment_date if payment_date is not None else date.today()
    return await settings_service.suggest_cheque_number(db, effective_date)


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> PaymentRead:
    try:
        payment = await payment_service.create_payment(db, payload)
    except payment_service.InvoiceNotFoundError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "INVOICE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise api_error(status.HTTP_400_BAD_REQUEST, "PAYMENT_INVALID", str(exc)) from exc
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
        raise not_found("Payment")
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
        raise api_error(status.HTTP_404_NOT_FOUND, "PAYMENT_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise api_error(status.HTTP_400_BAD_REQUEST, "PAYMENT_INVALID", str(exc)) from exc
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
        raise not_found("Payment")
    detail = {
        "invoice_id": payment.invoice_id,
        "amount": str(payment.amount),
        "method": payment.method,
    }
    try:
        await payment_service.delete_payment(db, payment_id)
    except payment_service.PaymentDeleteError as exc:
        raise conflict("PAYMENT_CONFLICT", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.PAYMENT_DELETED,
        actor=current_user,
        target_id=payment_id,
        target_type="payment",
        detail=detail,
    )


@router.post("/{payment_id}/fix-deposit-date", response_model=PaymentRead)
async def fix_deposit_date(
    payment_id: int,
    deposit_date: date,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> PaymentRead:
    """Correct a cheque payment with deposited=True but missing deposit_date."""
    try:
        updated = await payment_service.fix_inconsistent_deposit_date(db, payment_id, deposit_date)
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "PAYMENT_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise api_error(status.HTTP_400_BAD_REQUEST, "PAYMENT_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.PAYMENT_UPDATED,
        actor=current_user,
        target_id=payment_id,
        target_type="payment",
        detail={"deposit_date": str(deposit_date), "fix": "inconsistent_deposit_date"},
    )
    return updated
