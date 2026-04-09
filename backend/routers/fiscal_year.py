"""Fiscal years API — CRUD, pre-close checks, close, and open new FY."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import get_current_user, require_role
from backend.schemas.fiscal_year import FiscalYearCreate, FiscalYearRead
from backend.services import fiscal_year_service
from backend.services.fiscal_year_service import FiscalYearError

router = APIRouter(prefix="/accounting/fiscal-years", tags=["accounting"])

_AdminAccess = Annotated[
    User,
    Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN)),
]
_ReadAccess = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=list[FiscalYearRead])
async def list_fiscal_years(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> list[FiscalYearRead]:
    fys = await fiscal_year_service.list_fiscal_years(db)
    return fys  # type: ignore[return-value]


@router.get("/current", response_model=FiscalYearRead | None)
async def get_current(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> FiscalYearRead | None:
    return await fiscal_year_service.get_current_fiscal_year(db)  # type: ignore[return-value]


@router.post("/", response_model=FiscalYearRead, status_code=status.HTTP_201_CREATED)
async def create_fiscal_year(
    payload: FiscalYearCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminAccess,
) -> FiscalYearRead:
    fy = await fiscal_year_service.create_fiscal_year(db, payload)
    return fy  # type: ignore[return-value]


@router.get("/{fy_id}", response_model=FiscalYearRead)
async def get_fiscal_year(
    fy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> FiscalYearRead:
    fy = await fiscal_year_service.get_fiscal_year(db, fy_id)
    if fy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal year not found")
    return fy  # type: ignore[return-value]


@router.get("/{fy_id}/pre-close-checks", response_model=list[str])
async def pre_close_checks(
    fy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminAccess,
) -> list[str]:
    """Return a list of warning messages before closing a fiscal year.

    Empty list means no issues found.
    """
    fy = await fiscal_year_service.get_fiscal_year(db, fy_id)
    if fy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal year not found")
    return await fiscal_year_service.pre_close_checks(db, fy)


@router.post("/{fy_id}/close", response_model=FiscalYearRead)
async def close_fiscal_year(
    fy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminAccess,
) -> FiscalYearRead:
    fy = await fiscal_year_service.get_fiscal_year(db, fy_id)
    if fy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal year not found")
    try:
        closed = await fiscal_year_service.close_fiscal_year(db, fy)
    except FiscalYearError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return closed  # type: ignore[return-value]


@router.post(
    "/{fy_id}/open-next",
    response_model=FiscalYearRead,
    status_code=status.HTTP_201_CREATED,
)
async def open_new_fiscal_year(
    fy_id: int,
    payload: FiscalYearCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _AdminAccess,
) -> FiscalYearRead:
    """Open a new fiscal year from a closed one, generating report-à-nouveau entries."""
    closed_fy = await fiscal_year_service.get_fiscal_year(db, fy_id)
    if closed_fy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal year not found")
    try:
        new_fy = await fiscal_year_service.open_new_fiscal_year(db, closed_fy, payload)
    except FiscalYearError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return new_fy  # type: ignore[return-value]
