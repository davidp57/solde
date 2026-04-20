"""Bank API router — transactions, CSV import, deposit slips and reconciliation."""

from datetime import date
from decimal import Decimal
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.bank import BankTransaction
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.bank import (
    BankBalanceRead,
    BankTransactionClientPaymentCreate,
    BankTransactionClientPaymentLink,
    BankTransactionClientPaymentLinks,
    BankTransactionClientPaymentsCreate,
    BankTransactionCreate,
    BankTransactionRead,
    BankTransactionUpdate,
    DepositCreate,
    DepositRead,
)
from backend.services import bank_service
from backend.services.bank_import import (
    BankImportError,
    parse_credit_mutuel_csv,
    parse_ofx,
    parse_qif,
)

router = APIRouter(prefix="/bank", tags=["bank"])

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]


async def _serialize_transaction(
    db: AsyncSession,
    tx: BankTransaction,
) -> BankTransactionRead:
    payment_ids = await bank_service.get_transaction_payment_ids(db, tx.id)
    return BankTransactionRead.model_validate(tx).model_copy(update={"payment_ids": payment_ids})


async def _serialize_transactions(
    db: AsyncSession,
    txs: list[BankTransaction],
) -> list[BankTransactionRead]:
    return [await _serialize_transaction(db, tx) for tx in txs]


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


@router.get("/balance", response_model=BankBalanceRead)
async def get_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
) -> BankBalanceRead:
    balance = await bank_service.get_bank_balance(db)
    return BankBalanceRead(balance=balance)


@router.get("/transactions", response_model=list[BankTransactionRead])
async def list_transactions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    unreconciled_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
) -> list[BankTransactionRead]:
    txs = await bank_service.list_transactions(
        db,
        from_date=from_date,
        to_date=to_date,
        unreconciled_only=unreconciled_only,
        skip=skip,
        limit=limit,
    )
    return await _serialize_transactions(db, txs)


@router.post(
    "/transactions",
    response_model=BankTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_transaction(
    payload: BankTransactionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> BankTransactionRead:
    tx = await bank_service.add_transaction(db, payload)
    return await _serialize_transaction(db, tx)


@router.put("/transactions/{tx_id}", response_model=BankTransactionRead)
async def update_transaction(
    tx_id: int,
    payload: BankTransactionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> BankTransactionRead:
    tx = await bank_service.get_transaction(db, tx_id)
    if tx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    updated = await bank_service.update_transaction(db, tx, payload)
    return await _serialize_transaction(db, updated)


@router.post(
    "/transactions/{tx_id}/create-client-payment",
    response_model=BankTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_client_payment_from_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.create_client_payment_from_transaction(
            db,
            tx_id=tx_id,
            invoice_id=payload.invoice_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
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
    _current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.create_client_payments_from_transaction(
            db,
            tx_id=tx_id,
            payload=payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
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
    _current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.create_supplier_payment_from_transaction(
            db,
            tx_id=tx_id,
            invoice_id=payload.invoice_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return await _serialize_transaction(db, tx)


@router.post("/transactions/{tx_id}/link-client-payment", response_model=BankTransactionRead)
async def link_client_payment_to_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentLink,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.link_client_payment_to_transaction(
            db,
            tx_id=tx_id,
            payment_id=payload.payment_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return await _serialize_transaction(db, tx)


@router.post("/transactions/{tx_id}/link-client-payments", response_model=BankTransactionRead)
async def link_client_payments_to_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentLinks,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.link_client_payments_to_transaction(
            db,
            tx_id=tx_id,
            payment_ids=payload.payment_ids,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return await _serialize_transaction(db, tx)


@router.post("/transactions/{tx_id}/link-supplier-payment", response_model=BankTransactionRead)
async def link_supplier_payment_to_transaction(
    tx_id: int,
    payload: BankTransactionClientPaymentLink,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> BankTransactionRead:
    try:
        tx = await bank_service.link_supplier_payment_to_transaction(
            db,
            tx_id=tx_id,
            payment_id=payload.payment_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return await _serialize_transaction(db, tx)


# ---------------------------------------------------------------------------
# CSV import (Crédit Mutuel)
# ---------------------------------------------------------------------------


class _CsvImportBody(BankTransactionCreate):
    """Not used directly — import uses raw JSON body for flexibility."""


class _CsvImportRequest:
    content: str


class CsvImportRequest(BaseModel):
    content: str  # raw CSV text


@router.post(
    "/transactions/import-csv",
    response_model=list[BankTransactionRead],
    status_code=status.HTTP_201_CREATED,
)
async def import_csv(
    payload: CsvImportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> list[BankTransactionRead]:
    """Import transactions from a Crédit Mutuel CSV export."""
    try:
        rows = parse_credit_mutuel_csv(payload.content)
    except BankImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    created: list[BankTransactionRead] = []
    for row in rows:
        tx_payload = BankTransactionCreate(
            date=cast(date, row["date"]),
            amount=cast(Decimal, row["amount"]),
            balance_after=cast(Decimal, row["balance_after"]),
            description=str(row.get("description", "")),
            reference=cast(str | None, row.get("reference")),
            source="import",
        )
        tx = await bank_service.add_transaction(db, tx_payload)
        created.append(await _serialize_transaction(db, tx))
    return created


async def _import_rows(
    rows: list[dict[str, object]],
    db: AsyncSession,
) -> list[BankTransactionRead]:
    """Persist parsed bank transaction rows and return the created records."""
    created: list[BankTransactionRead] = []
    for row in rows:
        tx_payload = BankTransactionCreate(
            date=cast(date, row["date"]),
            amount=cast(Decimal, row["amount"]),
            balance_after=cast(Decimal, row["balance_after"]),
            description=str(row.get("description", "")),
            reference=cast(str | None, row.get("reference")),
            source="import",
        )
        tx = await bank_service.add_transaction(db, tx_payload)
        created.append(await _serialize_transaction(db, tx))
    return created


class OFXImportRequest(BaseModel):
    content: str  # raw OFX/QFX text


class QIFImportRequest(BaseModel):
    content: str  # raw QIF text


@router.post(
    "/transactions/import-ofx",
    response_model=list[BankTransactionRead],
    status_code=status.HTTP_201_CREATED,
)
async def import_ofx(
    payload: OFXImportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> list[BankTransactionRead]:
    """Import transactions from an OFX/QFX bank statement export."""
    try:
        rows = parse_ofx(payload.content)
    except BankImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return await _import_rows(rows, db)


@router.post(
    "/transactions/import-qif",
    response_model=list[BankTransactionRead],
    status_code=status.HTTP_201_CREATED,
)
async def import_qif(
    payload: QIFImportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> list[BankTransactionRead]:
    """Import transactions from a QIF bank statement export."""
    try:
        rows = parse_qif(payload.content)
    except BankImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return await _import_rows(rows, db)


# ---------------------------------------------------------------------------
# Deposit slips
# ---------------------------------------------------------------------------


@router.get("/deposits", response_model=list[DepositRead])
async def list_deposits(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
) -> list[DepositRead]:
    deposits = await bank_service.list_deposits(
        db,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )
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
                payment_ids=pids,
            )
        )
    return result


@router.post("/deposits", response_model=DepositRead, status_code=status.HTTP_201_CREATED)
async def create_deposit(
    payload: DepositCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: _WriteAccess,
) -> DepositRead:
    try:
        deposit = await bank_service.create_deposit(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    pids = await bank_service.get_deposit_payment_ids(db, deposit.id)
    return DepositRead(
        id=deposit.id,
        date=deposit.date,
        type=deposit.type,
        total_amount=deposit.total_amount,
        bank_reference=deposit.bank_reference,
        notes=deposit.notes,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deposit not found")
    pids = await bank_service.get_deposit_payment_ids(db, deposit_id)
    return DepositRead(
        id=deposit.id,
        date=deposit.date,
        type=deposit.type,
        total_amount=deposit.total_amount,
        bank_reference=deposit.bank_reference,
        notes=deposit.notes,
        payment_ids=pids,
    )
