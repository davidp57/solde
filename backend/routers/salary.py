"""Salaries API — CRUD for monthly salary records."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.routers.auth import require_role
from backend.schemas.salary import (
    SalaryCreate,
    SalaryRead,
    SalarySummaryRow,
    SalaryUpdate,
)
from backend.services import salary_service

if TYPE_CHECKING:
    from backend.models.salary import Salary

router = APIRouter(prefix="/salaries", tags=["salaries"])

_WriteAccess = Annotated[User, Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN))]
_ReadAccess = Annotated[
    User,
    Depends(require_role(UserRole.TRESORIER, UserRole.ADMIN)),
]


def _to_read(salary: "Salary") -> SalaryRead:
    from backend.services.salary_service import _employee_display_name  # noqa: PLC0415

    return SalaryRead(
        id=salary.id,
        employee_id=salary.employee_id,
        employee_name=_employee_display_name(salary.employee),
        month=salary.month,
        hours=salary.hours,
        gross=salary.gross,
        employee_charges=salary.employee_charges,
        employer_charges=salary.employer_charges,
        tax=salary.tax,
        net_pay=salary.net_pay,
        total_cost=salary.total_cost,
        notes=salary.notes,
        created_at=salary.created_at,
    )


@router.get("/", response_model=list[SalaryRead])
async def list_salaries(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    employee_id: int | None = Query(default=None),
    month: str | None = Query(default=None),
    from_month: str | None = Query(default=None),
    to_month: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
) -> list[SalaryRead]:
    salaries = await salary_service.list_salaries(
        db,
        employee_id=employee_id,
        month=month,
        from_month=from_month,
        to_month=to_month,
        skip=skip,
        limit=limit,
    )
    return [_to_read(s) for s in salaries]


@router.get("/summary", response_model=list[SalarySummaryRow])
async def get_monthly_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
    from_month: str | None = Query(default=None),
    to_month: str | None = Query(default=None),
) -> list[SalarySummaryRow]:
    return await salary_service.get_monthly_summary(
        db,
        from_month=from_month,
        to_month=to_month,
    )


@router.post("/", response_model=SalaryRead, status_code=status.HTTP_201_CREATED)
async def create_salary(
    payload: SalaryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> SalaryRead:
    salary = await salary_service.create_salary(db, payload)
    return _to_read(salary)


@router.get("/{salary_id}", response_model=SalaryRead)
async def get_salary(
    salary_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _ReadAccess,
) -> SalaryRead:
    salary = await salary_service.get_salary(db, salary_id)
    if salary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary not found")
    return _to_read(salary)


@router.put("/{salary_id}", response_model=SalaryRead)
async def update_salary(
    salary_id: int,
    payload: SalaryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> SalaryRead:
    salary = await salary_service.get_salary(db, salary_id)
    if salary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary not found")
    updated = await salary_service.update_salary(db, salary, payload)
    return _to_read(updated)


@router.delete("/{salary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_salary(
    salary_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: _WriteAccess,
) -> None:
    salary = await salary_service.get_salary(db, salary_id)
    if salary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary not found")
    await salary_service.delete_salary(db, salary)
