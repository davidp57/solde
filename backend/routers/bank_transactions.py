"""Bank transactions sub-router — CRUD, reconciliation, payment linking."""

import logging
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import api_error, conflict, not_found, unprocessable
from backend.models.bank import BankAccountType, BankTransaction
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.bank import (
    BankBalanceRead,
    BankReconcileBulkRequest,
    BankTransactionClientPaymentCreate,
    BankTransactionClientPaymentLink,
    BankTransactionClientPaymentLinks,
    BankTransactionClientPaymentsCreate,
    BankTransactionCreate,
    BankTransactionDepositMerge,
    BankTransactionRead,
    BankTransactionUpdate,
)
from backend.services import bank_service
from backend.services.audit_service import AuditAction, record_audit

logger = logging.getLogger(__name__)

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
# Shared serialization helpers (also used by bank_import)
# ---------------------------------------------------------------------------


def _serialize_transaction_with_payment_ids(
    tx: BankTransaction,
    payment_ids: list[int],
) -> BankTransactionRead:
    return BankTransactionRead.model_validate(tx).model_copy(update={"payment_ids": payment_ids})


async def _serialize_transaction(
    db: AsyncSession,
    tx: BankTransaction,
) -> BankTransactionRead:
    payment_ids = await bank_service.get_transaction_payment_ids(db, tx.id)
    return _serialize_transaction_with_payment_ids(tx, payment_ids)


async def _serialize_transactions(
    db: AsyncSession,
    txs: list[BankTransaction],
) -> list[BankTransactionRead]:
    if not txs:
        return []

    payment_ids_by_tx_id = await bank_service.get_transaction_payment_ids_map(
        db,
        [tx.id for tx in txs],
    )
    return [
        _serialize_transaction_with_payment_ids(tx, payment_ids_by_tx_id.get(tx.id, []))
        for tx in txs
    ]


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


@router.get("/balance", response_model=BankBalanceRead)
async def get_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> BankBalanceRead:
    balance_data = await bank_service.get_bank_balance(db)
    return BankBalanceRead(**balance_data)


@router.get("/chart/funds")
async def get_funds_chart(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    months: int = Query(default=6, ge=1, le=24),
) -> list[dict[str, Decimal | str]]:
    return await bank_service.get_monthly_funds_series(db, months=months)


@router.get("/transactions", response_model=list[BankTransactionRead])
async def list_transactions(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    unreconciled_only: bool = Query(default=False),
    bank_account: BankAccountType | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=1000, ge=1, le=5000),
) -> list[BankTransactionRead]:
    txs = await bank_service.list_transactions(
        db,
        from_date=from_date,
        to_date=to_date,
        unreconciled_only=unreconciled_only,
        bank_account=bank_account,
        skip=skip,
        limit=limit,
    )
    total = await bank_service.count_transactions(
        db,
        from_date=from_date,
        to_date=to_date,
        unreconciled_only=unreconciled_only,
        bank_account=bank_account,
    )
    response.headers["X-Total-Count"] = str(total)
    return await _serialize_transactions(db, txs)


@router.post(
    "/transactions",
    response_model=BankTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_transaction(
    payload: BankTransactionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    tx = await bank_service.add_transaction(db, payload)
    if tx is None:
        raise conflict(
            "BANK_TRANSACTION_DUPLICATE",
            "A transaction with this reference already exists",
        )
    await record_audit(
        db,
        action=AuditAction.BANK_TRANSACTION_CREATED,
        actor=current_user,
        target_id=tx.id,
        target_type="bank_transaction",
        detail={"date": str(tx.date), "amount": str(tx.amount)},
    )
    return await _serialize_transaction(db, tx)


@router.put("/transactions/{tx_id}", response_model=BankTransactionRead)
async def update_transaction(
    tx_id: int,
    payload: BankTransactionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    tx = await bank_service.get_transaction(db, tx_id)
    if tx is None:
        raise not_found("Transaction")
    # date/amount/bank_account can only be changed on manual transactions
    manual_only_fields = {
        k for k in ("date", "amount", "bank_account") if payload.model_fields_set.intersection({k})
    }
    if manual_only_fields and tx.source not in (
        "manual",
        "system_opening",
    ):
        raise unprocessable(
            "BANK_TRANSACTION_NOT_MANUAL",
            "date, amount and bank_account can only be updated on manual transactions",
        )
    # A reconciled transaction is locked accounting-wise: editing the fields that
    # drive its generated entries (date, amount, account, category) would leave the
    # journal stale. Mirror the delete guard — it must be unreconciled first.
    accounting_fields = {
        k
        for k in ("date", "amount", "bank_account", "detected_category")
        if k in payload.model_fields_set
    }
    if accounting_fields and tx.reconciled:
        raise unprocessable(
            "BANK_TRANSACTION_RECONCILED_LOCKED",
            "A reconciled transaction's date, amount, account or category cannot be "
            "edited; unreconcile it first",
        )
    updated = await bank_service.update_transaction(db, tx, payload)
    await record_audit(
        db,
        action=AuditAction.BANK_TRANSACTION_UPDATED,
        actor=current_user,
        target_id=tx_id,
        target_type="bank_transaction",
    )
    return await _serialize_transaction(db, updated)


@router.delete("/transactions/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    tx_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> None:
    tx = await bank_service.get_transaction(db, tx_id)
    if tx is None:
        raise not_found("Transaction")
    try:
        await bank_service.delete_manual_transaction(db, tx)
    except ValueError as exc:
        raise unprocessable(
            "BANK_TRANSACTION_DELETE_FAILED",
            str(exc),
        ) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_TRANSACTION_DELETED,
        actor=current_user,
        target_id=tx_id,
        target_type="bank_transaction",
    )


@router.post("/transactions/reconcile-bulk", response_model=int)
async def reconcile_transactions_bulk(
    payload: BankReconcileBulkRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> int:
    """Mark a batch of transactions as reconciled in a single request."""
    count = await bank_service.reconcile_transactions_bulk(db, ids=payload.ids)
    await record_audit(
        db,
        action=AuditAction.BANK_TRANSACTION_BULK_RECONCILED,
        actor=current_user,
        target_type="bank_transaction",
        detail={"count": count},
    )
    return count


@router.post(
    "/transactions/{tx_id}/create-client-payment",
    response_model=BankTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_client_payment_from_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.create_client_payment_from_transaction(
            db,
            tx_id=tx_id,
            invoice_id=payload.invoice_id,
        )
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "BANK_RESOURCE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_PAYMENT_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_PAYMENT_CREATED,
        actor=current_user,
        target_id=tx_id,
        target_type="bank_transaction",
        detail={"invoice_id": payload.invoice_id, "type": "client"},
    )
    return await _serialize_transaction(db, tx)


@router.post(
    "/transactions/{tx_id}/create-client-payments",
    response_model=BankTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_client_payments_from_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentsCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.create_client_payments_from_transaction(
            db,
            tx_id=tx_id,
            payload=payload,
        )
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "BANK_RESOURCE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_PAYMENT_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_PAYMENT_CREATED,
        actor=current_user,
        target_id=tx_id,
        target_type="bank_transaction",
        detail={"type": "client_multi"},
    )
    return await _serialize_transaction(db, tx)


@router.post(
    "/transactions/{tx_id}/create-supplier-payment",
    response_model=BankTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_supplier_payment_from_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.create_supplier_payment_from_transaction(
            db,
            tx_id=tx_id,
            invoice_id=payload.invoice_id,
        )
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "BANK_RESOURCE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_PAYMENT_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_PAYMENT_CREATED,
        actor=current_user,
        target_id=tx_id,
        target_type="bank_transaction",
        detail={"invoice_id": payload.invoice_id, "type": "supplier"},
    )
    return await _serialize_transaction(db, tx)


@router.post("/transactions/{tx_id}/link-client-payment", response_model=BankTransactionRead)
async def link_client_payment_to_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentLink,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.link_client_payment_to_transaction(
            db,
            tx_id=tx_id,
            payment_id=payload.payment_id,
        )
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "BANK_RESOURCE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_PAYMENT_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_PAYMENT_CREATED,
        actor=current_user,
        target_id=tx_id,
        target_type="bank_transaction",
        detail={"payment_id": payload.payment_id, "type": "link_client"},
    )
    return await _serialize_transaction(db, tx)


@router.post("/transactions/{tx_id}/link-client-payments", response_model=BankTransactionRead)
async def link_client_payments_to_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentLinks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.link_client_payments_to_transaction(
            db,
            tx_id=tx_id,
            payment_ids=payload.payment_ids,
        )
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "BANK_RESOURCE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_PAYMENT_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_PAYMENT_CREATED,
        actor=current_user,
        target_id=tx_id,
        target_type="bank_transaction",
        detail={"count": len(payload.payment_ids), "type": "link_client_multi"},
    )
    return await _serialize_transaction(db, tx)


@router.post("/transactions/{tx_id}/link-supplier-payment", response_model=BankTransactionRead)
async def link_supplier_payment_to_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentLink,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.link_supplier_payment_to_transaction(
            db,
            tx_id=tx_id,
            payment_id=payload.payment_id,
        )
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "BANK_RESOURCE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_PAYMENT_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_PAYMENT_CREATED,
        actor=current_user,
        target_id=tx_id,
        target_type="bank_transaction",
        detail={"payment_id": payload.payment_id, "type": "link_supplier"},
    )
    return await _serialize_transaction(db, tx)


@router.get(
    "/transactions/{tx_id}/deposit-merge-candidates",
    response_model=list[BankTransactionRead],
)
async def list_deposit_merge_candidates(
    tx_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> list[BankTransactionRead]:
    """Provisional deposit lines this statement row could be folded into."""
    try:
        candidates = await bank_service.list_deposit_merge_candidates(db, tx_id=tx_id)
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "BANK_RESOURCE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_DEPOSIT_MERGE_INVALID", str(exc)) from exc
    return await _serialize_transactions(db, candidates)


@router.post("/transactions/{tx_id}/merge-deposit", response_model=BankTransactionRead)
async def merge_deposit_transaction(
    tx_id: int,
    payload: BankTransactionDepositMerge,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankTransactionRead:
    """Fold this statement row into the provisional deposit line the user designated."""
    try:
        tx = await bank_service.merge_deposit_transaction(
            db,
            tx_id=tx_id,
            provisional_tx_id=payload.provisional_tx_id,
        )
    except LookupError as exc:
        raise api_error(status.HTTP_404_NOT_FOUND, "BANK_RESOURCE_NOT_FOUND", str(exc)) from exc
    except ValueError as exc:
        raise unprocessable("BANK_DEPOSIT_MERGE_INVALID", str(exc)) from exc
    await record_audit(
        db,
        action=AuditAction.BANK_DEPOSIT_MERGED,
        actor=current_user,
        target_id=tx.id,
        target_type="bank_transaction",
        detail={"absorbed_tx_id": tx_id},
    )
    return await _serialize_transaction(db, tx)
