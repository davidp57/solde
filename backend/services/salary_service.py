"""Salary service — CRUD and accounting entry generation."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.contact import Contact
from backend.models.salary import Salary
from backend.schemas.salary import (
    SalaryCreate,
    SalaryPreviousRead,
    SalarySummaryRow,
    SalaryUpdate,
    WorkforceCostRow,
)


class SalaryError(Exception):
    """Raised for invalid salary operations."""


async def list_salaries(
    db: AsyncSession,
    *,
    employee_id: int | None = None,
    month: str | None = None,
    from_month: str | None = None,
    to_month: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Salary]:
    query = (
        select(Salary)
        .options(selectinload(Salary.employee))
        .order_by(Salary.month.desc(), Salary.employee_id)
    )
    if employee_id is not None:
        query = query.where(Salary.employee_id == employee_id)
    if month is not None:
        query = query.where(Salary.month == month)
    if from_month is not None:
        query = query.where(Salary.month >= from_month)
    if to_month is not None:
        query = query.where(Salary.month <= to_month)
    query = query.offset(skip)
    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_salary(db: AsyncSession, salary_id: int) -> Salary | None:
    result = await db.execute(
        select(Salary).options(selectinload(Salary.employee)).where(Salary.id == salary_id)
    )
    return result.scalar_one_or_none()


async def create_salary(db: AsyncSession, payload: SalaryCreate) -> Salary:
    """Create a salary record and generate accounting entries."""
    salary = Salary(**payload.model_dump())
    db.add(salary)
    await db.flush()

    # Auto-generate accounting entries (no-op if rules not seeded)
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_salary,
    )

    await generate_entries_for_salary(db, salary)
    await db.commit()
    await db.refresh(salary)
    return salary


async def update_salary(db: AsyncSession, salary: Salary, payload: SalaryUpdate) -> Salary:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=False).items():
        if value is not None:
            setattr(salary, field, value)
    await db.commit()
    await db.refresh(salary)
    return salary


async def delete_salary(db: AsyncSession, salary: Salary) -> None:
    await db.delete(salary)
    await db.commit()


async def get_monthly_summary(
    db: AsyncSession,
    *,
    from_month: str | None = None,
    to_month: str | None = None,
) -> list[SalarySummaryRow]:
    """Return aggregated salary data grouped by month."""
    query = (
        select(
            Salary.month,
            func.sum(Salary.gross).label("total_gross"),
            func.sum(Salary.employee_charges).label("total_employee_charges"),
            func.sum(Salary.employer_charges).label("total_employer_charges"),
            func.sum(Salary.tax).label("total_tax"),
            func.sum(Salary.net_pay).label("total_net_pay"),
            func.count(Salary.id).label("count"),
        )
        .group_by(Salary.month)
        .order_by(Salary.month.desc())
    )
    if from_month is not None:
        query = query.where(Salary.month >= from_month)
    if to_month is not None:
        query = query.where(Salary.month <= to_month)
    result = await db.execute(query)
    rows = result.all()
    return [
        SalarySummaryRow(
            month=row.month,
            total_gross=Decimal(str(row.total_gross or 0)),
            total_employee_charges=Decimal(str(row.total_employee_charges or 0)),
            total_employer_charges=Decimal(str(row.total_employer_charges or 0)),
            total_tax=Decimal(str(row.total_tax or 0)),
            total_net_pay=Decimal(str(row.total_net_pay or 0)),
            total_cost=Decimal(str(row.total_gross or 0))
            + Decimal(str(row.total_employer_charges or 0)),
            count=row.count,
        )
        for row in rows
    ]


def _employee_display_name(contact: Contact | None) -> str | None:
    if contact is None:
        return None
    parts = []
    if contact.prenom:
        parts.append(contact.prenom)
    if contact.nom:
        parts.append(contact.nom)
    return " ".join(parts) if parts else None


async def get_previous_salary(db: AsyncSession, employee_id: int) -> SalaryPreviousRead | None:
    """Return pre-CEA fields from the most recent salary for an employee.

    Only hours, gross, and CDD breakdown components are returned — the CEA
    fields (cotisations, net) are intentionally excluded because they can
    change each month.
    """
    result = await db.execute(
        select(Salary)
        .where(Salary.employee_id == employee_id)
        .order_by(Salary.month.desc())
        .limit(1)
    )
    salary = result.scalar_one_or_none()
    if salary is None:
        return None
    return SalaryPreviousRead(
        employee_id=salary.employee_id,
        hours=salary.hours,
        gross=salary.gross,
        brut_declared=salary.brut_declared,
        conges_payes=salary.conges_payes,
        precarite=salary.precarite,
    )


async def get_workforce_cost(
    db: AsyncSession,
    *,
    from_month: str | None = None,
    to_month: str | None = None,
) -> list[WorkforceCostRow]:
    """Return consolidated workforce cost rows (employees + AE invoices) by month."""
    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415

    rows: list[WorkforceCostRow] = []

    # --- Employee salaries ---
    salary_query = (
        select(Salary)
        .options(selectinload(Salary.employee))
        .order_by(Salary.month, Salary.employee_id)
    )
    if from_month is not None:
        salary_query = salary_query.where(Salary.month >= from_month)
    if to_month is not None:
        salary_query = salary_query.where(Salary.month <= to_month)
    salary_result = await db.execute(salary_query)
    for sal in salary_result.scalars().all():
        emp = sal.employee
        contract = getattr(emp, "contract_type", None) or "CDI"
        person_type = contract.upper() if contract else "CDI"
        hours = sal.hours if sal.hours and sal.hours > 0 else None
        total_cost = sal.total_cost
        rows.append(
            WorkforceCostRow(
                month=sal.month,
                person_id=emp.id if emp else sal.employee_id,
                person_name=_employee_display_name(emp) or str(sal.employee_id),
                person_type=person_type,
                hours=hours,
                amount=sal.gross,
                total_cost=total_cost,
                hourly_cost=(total_cost / hours).quantize(Decimal("0.01"))
                if hours and hours > 0
                else None,
            )
        )

    # --- AE / contractor invoices ---
    ae_query = (
        select(Invoice)
        .options(selectinload(Invoice.contact))
        .where(Invoice.type == InvoiceType.FOURNISSEUR)
        .where(Invoice.contact.has(Contact.is_contractor.is_(True)))
        .order_by(Invoice.date)
    )
    ae_result = await db.execute(ae_query)
    for inv in ae_result.scalars().all():
        # Map invoice date to YYYY-MM month string
        month_str = inv.date.strftime("%Y-%m")
        if from_month and month_str < from_month:
            continue
        if to_month and month_str > to_month:
            continue
        contact = inv.contact
        hours = inv.hours if inv.hours and inv.hours > 0 else None
        rows.append(
            WorkforceCostRow(
                month=month_str,
                person_id=contact.id if contact else inv.contact_id,
                person_name=_employee_display_name(contact) or str(inv.contact_id),
                person_type="AE",
                hours=hours,
                amount=inv.total_amount,
                total_cost=inv.total_amount,
                hourly_cost=(inv.total_amount / hours).quantize(Decimal("0.01"))
                if hours and hours > 0
                else None,
            )
        )

    rows.sort(key=lambda r: (r.month, r.person_name))
    return rows
