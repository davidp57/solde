"""Fiscal year service — CRUD, pre-close checks, closing, and report à nouveau."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.schemas.fiscal_year import FiscalYearCreate


class FiscalYearError(Exception):
    """Raised for invalid fiscal year operations."""


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Pre-close checks
# ---------------------------------------------------------------------------


async def pre_close_checks(db: AsyncSession, fy: FiscalYear) -> list[str]:
    """Run sanity checks before closing a fiscal year.

    Returns a list of warning messages (empty = all clear).
    """

    warnings: list[str] = []

    if fy.status != FiscalYearStatus.OPEN:
        warnings.append(
            f"L'exercice '{fy.name}' n'est pas ouvert (statut : {fy.status})."
        )
        return warnings  # no further checks possible

    # Check 1: total debits == total credits for this FY
    entries_result = await db.execute(
        select(AccountingEntry).where(AccountingEntry.fiscal_year_id == fy.id)
    )
    entries = entries_result.scalars().all()
    total_debit = sum(Decimal(str(e.debit)) for e in entries)
    total_credit = sum(Decimal(str(e.credit)) for e in entries)
    if total_debit != total_credit:
        warnings.append(
            f"Balance déséquilibrée : total débit {total_debit} ≠ total crédit {total_credit}."
        )

    # Check 2: entries without fiscal year assigned (orphans)
    orphans = await db.execute(
        select(AccountingEntry).where(AccountingEntry.fiscal_year_id.is_(None))
    )
    orphan_count = len(orphans.scalars().all())
    if orphan_count > 0:
        warnings.append(
            f"{orphan_count} écriture(s) sans exercice associé — vérifier avant clôture."
        )

    return warnings


# ---------------------------------------------------------------------------
# Close fiscal year (enhanced)
# ---------------------------------------------------------------------------


async def close_fiscal_year(db: AsyncSession, fy: FiscalYear) -> FiscalYear:
    """Close a fiscal year:

    1. Compute net result from accounting entries scoped to this FY.
    2. Create a CLOTURE entry for the result (120000 excédent / 129000 déficit).
    3. Mark the fiscal year as CLOSED.
    """
    if fy.status != FiscalYearStatus.OPEN:
        raise FiscalYearError("Only OPEN fiscal years can be closed")

    from backend.services.accounting_engine import _next_entry_number  # noqa: PLC0415
    from backend.services.accounting_entry_service import (  # noqa: PLC0415
        _compute_resultat,
    )

    charges, produits = await _compute_resultat(db, fy.id)
    resultat = produits - charges  # positive = excédent

    if resultat != Decimal("0"):
        result_account = "120000" if resultat >= 0 else "129000"
        abs_result = abs(resultat)

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


# ---------------------------------------------------------------------------
# Open new fiscal year with report à nouveau
# ---------------------------------------------------------------------------


async def open_new_fiscal_year(
    db: AsyncSession, closed_fy: FiscalYear, payload: FiscalYearCreate
) -> FiscalYear:
    """Create a new fiscal year and generate report-à-nouveau entries.

    For each actif/passif account with a non-zero solde in the closed FY,
    a CLOTURE entry is added to the new FY to carry the balance forward.
    """
    if closed_fy.status != FiscalYearStatus.CLOSED:
        raise FiscalYearError("Source fiscal year must be CLOSED to open a new one")

    # Create new FY
    new_fy = FiscalYear(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=FiscalYearStatus.OPEN,
    )
    db.add(new_fy)
    await db.flush()

    # Compute balance of actif/passif accounts for the closed FY
    from backend.models.accounting_account import (
        AccountingAccount,
        AccountType,
    )  # noqa: PLC0415
    from backend.services.accounting_engine import _next_entry_number  # noqa: PLC0415

    entries_result = await db.execute(
        select(AccountingEntry).where(AccountingEntry.fiscal_year_id == closed_fy.id)
    )
    entries = entries_result.scalars().all()

    # Get actif/passif account numbers
    acct_result = await db.execute(
        select(AccountingAccount).where(
            AccountingAccount.type.in_([AccountType.ACTIF, AccountType.PASSIF])
        )
    )
    acct_map = {a.number: a for a in acct_result.scalars().all()}

    # Aggregate solde per balance account
    soldes: dict[str, Decimal] = {}
    for e in entries:
        if e.account_number not in acct_map:
            continue
        soldes[e.account_number] = (
            soldes.get(e.account_number, Decimal("0"))
            + Decimal(str(e.debit))
            - Decimal(str(e.credit))
        )

    # Generate RAN entries
    ran_date = new_fy.start_date
    for account_number, solde in soldes.items():
        if solde == Decimal("0"):
            continue
        acct = acct_map[account_number]
        is_debit = solde > 0
        abs_solde = abs(solde)
        num = await _next_entry_number(db)
        db.add(
            AccountingEntry(
                entry_number=num,
                date=ran_date,
                account_number=account_number,
                label=f"RAN {closed_fy.name} — {acct.label}",
                debit=abs_solde if is_debit else Decimal("0"),
                credit=abs_solde if not is_debit else Decimal("0"),
                fiscal_year_id=new_fy.id,
                source_type=EntrySourceType.CLOTURE,
                source_id=closed_fy.id,
            )
        )

    await db.commit()
    await db.refresh(new_fy)
    return new_fy
