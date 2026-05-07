"""Bank import sub-router — CSV, OFX, QIF file import."""

import logging
from datetime import date
from decimal import Decimal
from typing import Annotated, cast

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.errors import unprocessable
from backend.models.bank import BankAccountType, BankTransactionSource
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.routers.bank_transactions import _serialize_transaction
from backend.schemas.bank import (
    BankImportResult,
    BankTransactionCreate,
    BankTransactionRead,
)
from backend.services import bank_service
from backend.services import settings as settings_service
from backend.services.audit_service import AuditAction, record_audit
from backend.services.bank_import import (
    BankImportError,
    parse_credit_mutuel_csv,
    parse_ofx,
    parse_qif,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.SECRETAIRE, UserRole.TRESORIER, UserRole.ADMIN)),
]


# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------


class CsvImportRequest(BaseModel):
    content: str  # raw CSV text


class OFXImportRequest(BaseModel):
    content: str  # raw OFX/QFX text
    default_bank_account: BankAccountType = BankAccountType.COURANT


class QIFImportRequest(BaseModel):
    content: str  # raw QIF text


async def _import_rows(
    rows: list[dict[str, object]],
    db: AsyncSession,
    *,
    source: BankTransactionSource = BankTransactionSource.IMPORT,
) -> BankImportResult:
    """Persist parsed rows, skipping duplicates by reference. Returns created + skipped count."""
    created: list[BankTransactionRead] = []
    skipped = 0

    # For non-Excel imports, compute a per-account cut-off date based on the latest
    # Excel-imported transaction. Rows on or before that date are already covered.
    excel_cutoffs: dict[BankAccountType, date] = {}
    if source not in (BankTransactionSource.IMPORT_EXCEL, BankTransactionSource.IMPORT):
        excel_cutoffs = await bank_service.get_excel_cutoffs(db)
        if excel_cutoffs:
            logger.info(
                "Excel cut-off dates applied: %s",
                {k: str(v) for k, v in excel_cutoffs.items()},
            )

    for row in rows:
        raw_account = row.get("bank_account", "courant")
        bank_account = (
            BankAccountType(str(raw_account))
            if raw_account in (BankAccountType.COURANT, BankAccountType.EPARGNE)
            else BankAccountType.COURANT
        )
        tx_date = cast(date, row["date"])
        cutoff = excel_cutoffs.get(bank_account)
        if cutoff and tx_date <= cutoff:
            skipped += 1
            continue
        tx_payload = BankTransactionCreate(
            date=tx_date,
            amount=cast(Decimal, row["amount"]),
            balance_after=cast(Decimal, row["balance_after"]),
            description=str(row.get("description", "")),
            reference=cast(str | None, row.get("reference")),
            source=source,
            bank_account=bank_account,
        )
        tx = await bank_service.add_transaction(db, tx_payload)
        if tx is None:
            skipped += 1
        else:
            created.append(await _serialize_transaction(db, tx))
    return BankImportResult(created=created, skipped=skipped)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/transactions/import-csv",
    response_model=BankImportResult,
    status_code=status.HTTP_201_CREATED,
)
async def import_csv(
    payload: CsvImportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankImportResult:
    """Import transactions from a Crédit Mutuel CSV export."""
    try:
        rows = parse_credit_mutuel_csv(payload.content)
    except BankImportError as exc:
        logger.warning("CSV import rejected: %s", exc)
        raise unprocessable("BANK_IMPORT_PARSE_ERROR", str(exc)) from exc

    result = await _import_rows(rows, db, source=BankTransactionSource.IMPORT_CSV)
    await record_audit(
        db,
        action=AuditAction.BANK_IMPORTED,
        actor=current_user,
        target_type="bank_import",
        detail={"format": "csv", "count": len(result.created), "skipped": result.skipped},
    )
    return result


@router.post(
    "/transactions/import-ofx",
    response_model=BankImportResult,
    status_code=status.HTTP_201_CREATED,
)
async def import_ofx(
    payload: OFXImportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankImportResult:
    """Import transactions from an OFX/QFX bank statement export."""
    settings = await settings_service.get_settings(db)
    courant_acctid = settings.bank_account_courant_acctid if settings else None
    epargne_acctid = settings.bank_account_epargne_acctid if settings else None
    try:
        rows = parse_ofx(
            payload.content,
            courant_acctid=courant_acctid,
            epargne_acctid=epargne_acctid,
            default_bank_account=payload.default_bank_account,
        )
    except BankImportError as exc:
        logger.warning("OFX import rejected: %s", exc)
        raise unprocessable("BANK_IMPORT_PARSE_ERROR", str(exc)) from exc
    result = await _import_rows(rows, db, source=BankTransactionSource.IMPORT_OFX)
    await record_audit(
        db,
        action=AuditAction.BANK_IMPORTED,
        actor=current_user,
        target_type="bank_import",
        detail={"format": "ofx", "count": len(result.created), "skipped": result.skipped},
    )
    return result


@router.post(
    "/transactions/import-qif",
    response_model=BankImportResult,
    status_code=status.HTTP_201_CREATED,
)
async def import_qif(
    payload: QIFImportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: _WriteAccess,
) -> BankImportResult:
    """Import transactions from a QIF bank statement export."""
    try:
        rows = parse_qif(payload.content)
    except BankImportError as exc:
        logger.warning("QIF import rejected: %s", exc)
        raise unprocessable("BANK_IMPORT_PARSE_ERROR", str(exc)) from exc
    result = await _import_rows(rows, db, source=BankTransactionSource.IMPORT_QIF)
    await record_audit(
        db,
        action=AuditAction.BANK_IMPORTED,
        actor=current_user,
        target_type="bank_import",
        detail={"format": "qif", "count": len(result.created), "skipped": result.skipped},
    )
    return result
