"""Fiscal year service — CRUD and closing."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.schemas.fiscal_year import FiscalYearCreate


class FiscalYearError(Exception):
    """Raised for invalid fiscal year operations."""


async def list_fiscal_years(db: AsyncSession) -> list[FiscalYear]:
    result = await db.execute(select(FiscalYear).order_by(FiscalYear.start_date.desc()))
    return list(result.scalars().all())


async def get_fiscal_year(db: AsyncSession, fy_id: int) -> FiscalYear | None:
    result = await db.execute(select(FiscalYear).where(FiscalYear.id == fy_id))
    return result.scalar_one_or_none()


async def get_current_fiscal_year(db: AsyncSession) -> FiscalYear | None:
    """Return the first open fiscal year (the active one)."""
    result = await db.execute(
        select(FiscalYear)
        .where(FiscalYear.status == FiscalYearStatus.OPEN)
        .order_by(FiscalYear.start_date.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_fiscal_year(db: AsyncSession, payload: FiscalYearCreate) -> FiscalYear:
    fy = FiscalYear(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=FiscalYearStatus.OPEN,
    )
    db.add(fy)
    await db.commit()
    await db.refresh(fy)
    return fy


async def close_fiscal_year(db: AsyncSession, fy: FiscalYear) -> FiscalYear:
    """Close a fiscal year:

    1. Compute net result from accounting entries scoped to this FY.
    2. Create a CLOTURE entry posting the result to 120000 or 129000.
    3. Mark the fiscal year as CLOSED.
    """
    if fy.status != FiscalYearStatus.OPEN:
        raise FiscalYearError("Only OPEN fiscal years can be closed")

    from backend.services.accounting_entry_service import (  # noqa: PLC0415
        _compute_resultat,
    )

    charges, produits = await _compute_resultat(db, fy.id)
    resultat = produits - charges  # positive = excédent

    if resultat != Decimal("0"):
        # Determine the result account
        result_account = "120000" if resultat >= 0 else "129000"
        abs_result = abs(resultat)

        from backend.services.accounting_engine import _next_entry_number  # noqa: PLC0415

        # Charges C / result account D (if excédent) — standard closing
        # Produits D / result account C
        # Simplified: just record the net result as a single CLOTURE entry pair
        # Debit: 120000/129000, Credit: 110000 (report à nouveau via clôture)
        num1 = await _next_entry_number(db)
        db.add(
            AccountingEntry(
                entry_number=num1,
                date=fy.end_date,
                account_number=result_account,
                label=f"Résultat exercice {fy.name}",
                debit=abs_result if resultat >= 0 else Decimal("0"),
                credit=abs_result if resultat < 0 else Decimal("0"),
                fiscal_year_id=fy.id,
                source_type=EntrySourceType.CLOTURE,
                source_id=fy.id,
            )
        )

    fy.status = FiscalYearStatus.CLOSED
    await db.commit()
    await db.refresh(fy)
    return fy
