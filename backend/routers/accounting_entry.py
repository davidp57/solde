"""Accounting entries API — journal, balance, grand livre, compte de résultat, saisie manuelle."""

from datetime import date
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.accounting_entry import EntrySourceType
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.accounting_entry import (
    AccountingEntryGroupRead,
    AccountingEntryRead,
    BalanceRow,
    BilanRead,
    LedgerRead,
    ManualEntryCreate,
    ManualEntryUpdate,
    ResultatRead,
)
from backend.services import accounting_entry_service, export_service

router = APIRouter(prefix="/accounting/entries", tags=["accounting"])

_WriteAccess = Annotated[
    User,
    Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[
    User,
    Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN)),
]


@router.get("/journal", response_model=list[AccountingEntryRead])
async def get_journal(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    account_number: str | None = Query(default=None),
    source_type: EntrySourceType | None = Query(default=None),
    fiscal_year_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=5000, ge=1, le=10000),
) -> list[AccountingEntryRead]:
    return await accounting_entry_service.get_journal(
        db,
        from_date=from_date,
        to_date=to_date,
        account_number=account_number,
        source_type=source_type,
        fiscal_year_id=fiscal_year_id,
        skip=skip,
        limit=limit,
    )


@router.get("/journal-grouped", response_model=list[AccountingEntryGroupRead])
async def get_grouped_journal(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    account_number: str | None = Query(default=None),
    source_type: EntrySourceType | None = Query(default=None),
    fiscal_year_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=5000, ge=1, le=10000),
) -> list[AccountingEntryGroupRead]:
    return await accounting_entry_service.get_grouped_journal(
        db,
        from_date=from_date,
        to_date=to_date,
        account_number=account_number,
        source_type=source_type,
        fiscal_year_id=fiscal_year_id,
        skip=skip,
        limit=limit,
    )


@router.get("/balance", response_model=list[BalanceRow])
async def get_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    fiscal_year_id: int | None = Query(default=None),
) -> list[BalanceRow]:
    return await accounting_entry_service.get_balance(
        db, from_date=from_date, to_date=to_date, fiscal_year_id=fiscal_year_id
    )


@router.get("/ledger/{account_number}", response_model=LedgerRead)
async def get_ledger(
    account_number: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    fiscal_year_id: int = Query(...),
) -> LedgerRead:
    return await accounting_entry_service.get_ledger(
        db,
        account_number,
        from_date=from_date,
        to_date=to_date,
        fiscal_year_id=fiscal_year_id,
    )


@router.get("/resultat", response_model=ResultatRead)
async def get_resultat(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    fiscal_year_id: int | None = Query(default=None),
) -> ResultatRead:
    return await accounting_entry_service.get_resultat(db, fiscal_year_id=fiscal_year_id)


@router.post(
    "/manual",
    response_model=list[AccountingEntryRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_entry(
    payload: ManualEntryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> list[AccountingEntryRead]:
    debit, credit = await accounting_entry_service.create_manual_entry(db, payload)
    return cast(list[AccountingEntryRead], [debit, credit])


@router.put("/manual/{entry_id}", response_model=list[AccountingEntryRead])
async def update_manual_entry(
    entry_id: int,
    payload: ManualEntryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> list[AccountingEntryRead]:
    try:
        debit, credit = await accounting_entry_service.update_manual_entry(db, entry_id, payload)
    except ValueError as exc:
        detail = str(exc)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in detail
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return cast(list[AccountingEntryRead], [debit, credit])


@router.get("/bilan", response_model=BilanRead)
async def get_bilan(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    fiscal_year_id: int | None = Query(default=None),
) -> BilanRead:
    """Return a simplified balance sheet (actif / passif)."""
    return await accounting_entry_service.get_bilan(db, fiscal_year_id=fiscal_year_id)


# ---------------------------------------------------------------------------
# CSV export endpoints
# ---------------------------------------------------------------------------


@router.get("/journal/export/csv")
async def export_journal_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    account_number: str | None = Query(default=None),
    fiscal_year_id: int | None = Query(default=None),
) -> Response:
    """Download journal entries as CSV."""
    content = await export_service.export_journal_csv(
        db,
        from_date=from_date,
        to_date=to_date,
        account_number=account_number,
        fiscal_year_id=fiscal_year_id,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=journal.csv"},
    )


@router.get("/balance/export/csv")
async def export_balance_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    fiscal_year_id: int | None = Query(default=None),
) -> Response:
    """Download balance as CSV."""
    content = await export_service.export_balance_csv(
        db, from_date=from_date, to_date=to_date, fiscal_year_id=fiscal_year_id
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=balance.csv"},
    )


@router.get("/resultat/export/csv")
async def export_resultat_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    fiscal_year_id: int | None = Query(default=None),
) -> Response:
    """Download compte de résultat as CSV."""
    content = await export_service.export_resultat_csv(db, fiscal_year_id=fiscal_year_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=resultat.csv"},
    )


@router.get("/bilan/export/csv")
async def export_bilan_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    fiscal_year_id: int | None = Query(default=None),
) -> Response:
    """Download simplified bilan as CSV."""
    content = await export_service.export_bilan_csv(db, fiscal_year_id=fiscal_year_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=bilan.csv"},
    )
