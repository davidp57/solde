"""Fiscal year service — CRUD, pre-close checks, closing, and report à nouveau."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import (
    AccountingEntry,
    EntrySourceType,
    build_entry_group_key,
)
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
    """Return the open fiscal year covering today, else the latest open one."""
    today = date.today()
    result = await db.execute(
        select(FiscalYear)
        .where(
            FiscalYear.status == FiscalYearStatus.OPEN,
            FiscalYear.start_date <= today,
            FiscalYear.end_date >= today,
        )
        .order_by(FiscalYear.start_date.desc())
        .limit(1)
    )
    current_fiscal_year = result.scalar_one_or_none()
    if current_fiscal_year is not None:
        return current_fiscal_year

    fallback_result = await db.execute(
        select(FiscalYear)
        .where(FiscalYear.status == FiscalYearStatus.OPEN)
        .order_by(FiscalYear.start_date.desc())
        .limit(1)
    )
    return fallback_result.scalar_one_or_none()


async def find_fiscal_year_for_date(db: AsyncSession, target_date: date) -> FiscalYear | None:
    """Return the fiscal year covering a given date, if any."""
    result = await db.execute(
        select(FiscalYear)
        .where(FiscalYear.start_date <= target_date, FiscalYear.end_date >= target_date)
        .order_by(FiscalYear.start_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def find_fiscal_year_id_for_date(db: AsyncSession, target_date: date) -> int | None:
    """Return the ID of the fiscal year covering a given date, if any."""
    fiscal_year = await find_fiscal_year_for_date(db, target_date)
    return fiscal_year.id if fiscal_year is not None else None


async def _assert_no_overlap(db: AsyncSession, start_date: date, end_date: date) -> None:
    """Reject a period overlapping an existing fiscal year.

    Overlapping years would make ``find_fiscal_year_for_date`` ambiguous: entries
    would silently land in whichever year sorts first.
    """
    result = await db.execute(
        select(FiscalYear)
        .where(FiscalYear.start_date <= end_date, FiscalYear.end_date >= start_date)
        .order_by(FiscalYear.start_date.asc())
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise FiscalYearError(
            f"La période demandée chevauche l'exercice « {existing.name} » "
            f"({existing.start_date} → {existing.end_date})."
        )


async def create_fiscal_year(db: AsyncSession, payload: FiscalYearCreate) -> FiscalYear:
    await _assert_no_overlap(db, payload.start_date, payload.end_date)
    fy = FiscalYear(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=FiscalYearStatus.OPEN,
    )
    db.add(fy)
    await db.flush()
    await db.refresh(fy)
    return fy


# ---------------------------------------------------------------------------
# Pre-close checks
# ---------------------------------------------------------------------------


_MAX_REPORTED_UNBALANCED_GROUPS = 10


def _unbalanced_groups(entries: Sequence[AccountingEntry]) -> list[tuple[str, Decimal]]:
    """Return (label, gap) for each entry group whose debits differ from its credits.

    The label leans on the entries' own wording, which names the document far
    better than a raw group key would.
    """
    totals: dict[str, list[Decimal]] = {}
    labels: dict[str, str] = {}
    for entry in entries:
        key = entry.group_key or f"entry:{entry.id}"
        bucket = totals.setdefault(key, [Decimal("0"), Decimal("0")])
        bucket[0] += entry.debit
        bucket[1] += entry.credit
        labels.setdefault(key, entry.label or key)

    unbalanced = [
        (labels[key], debit - credit) for key, (debit, credit) in totals.items() if debit != credit
    ]
    unbalanced.sort(key=lambda item: abs(item[1]), reverse=True)
    return unbalanced[:_MAX_REPORTED_UNBALANCED_GROUPS]


def _distinct_labels(entries: Sequence[AccountingEntry]) -> list[str]:
    """Return the distinct entry labels, capped — entries of one document share a label."""
    seen: list[str] = []
    for entry in entries:
        label = entry.label or f"écriture #{entry.id}"
        if label not in seen:
            seen.append(label)
    return seen[:_MAX_REPORTED_UNBALANCED_GROUPS]


async def pre_close_checks(db: AsyncSession, fy: FiscalYear) -> list[str]:
    """Run sanity checks before closing a fiscal year.

    Returns a list of warning messages (empty = all clear).
    """

    warnings: list[str] = []

    if fy.status != FiscalYearStatus.OPEN:
        warnings.append(f"L'exercice '{fy.name}' n'est pas ouvert (statut : {fy.status}).")
        return warnings  # no further checks possible

    # Check 1: total debits == total credits for this FY
    entries_result = await db.execute(
        select(AccountingEntry).where(AccountingEntry.fiscal_year_id == fy.id)
    )
    entries = entries_result.scalars().all()
    total_debit = sum(e.debit for e in entries)
    total_credit = sum(e.credit for e in entries)
    if total_debit != total_credit:
        warnings.append(
            f"Balance déséquilibrée : total débit {total_debit} ≠ total crédit {total_credit}."
        )
        # Naming the offending documents turns an unusable total into something
        # actionable — the imbalance always comes from a handful of groups.
        for label, gap in _unbalanced_groups(entries):
            warnings.append(f"  ↳ {label} : écart de {gap}.")

    # Check 2: entries with no fiscal year *whose date falls in this period*.
    # Orphans dated outside it (imported history, entries written before the next
    # year was opened) carry no weight in this closing: they are excluded from the
    # result and from the balance. Reporting them would raise an alarm every year
    # for something this closing cannot fix — and an alarm nobody can act on is an
    # alarm everybody learns to skip.
    orphans_result = await db.execute(
        select(AccountingEntry).where(
            AccountingEntry.fiscal_year_id.is_(None),
            AccountingEntry.date >= fy.start_date,
            AccountingEntry.date <= fy.end_date,
        )
    )
    orphans = list(orphans_result.scalars().all())
    if orphans:
        warnings.append(
            f"{len(orphans)} écriture(s) datée(s) dans cet exercice mais non rattachée(s) — "
            "elles seront exclues du résultat."
        )
        for label in _distinct_labels(orphans):
            warnings.append(f"  ↳ {label}.")

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
                group_key=build_entry_group_key(EntrySourceType.CLOTURE, fy.id),
            )
        )

    fy.status = FiscalYearStatus.CLOSED
    await db.flush()
    await db.refresh(fy)
    return fy


async def administrative_close_fiscal_year(db: AsyncSession, fy: FiscalYear) -> FiscalYear:
    """Close a fiscal year without generating any closing entries.

    This mode is intended for historical periods imported from Excel where
    closing and carry-forward entries already exist in the imported journal.
    """
    if fy.status != FiscalYearStatus.OPEN:
        raise FiscalYearError("Only OPEN fiscal years can be administratively closed")

    fy.status = FiscalYearStatus.CLOSED
    await db.flush()
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
    await _assert_no_overlap(db, payload.start_date, payload.end_date)

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
    from backend.services.accounting_engine import next_entry_numbers  # noqa: PLC0415

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
        soldes[e.account_number] = soldes.get(e.account_number, Decimal("0")) + e.debit - e.credit

    # Generate RAN entries.
    # Numbers are allocated in one go: asking for the next number per iteration
    # reads MAX(entry_number) from the database, which does not move until the
    # flush — so every entry would claim the same number and the unique
    # constraint would blow up on the first year carrying more than one balance.
    ran_date = new_fy.start_date
    carried = [(number, solde) for number, solde in soldes.items() if solde != Decimal("0")]
    entry_numbers = await next_entry_numbers(db, len(carried))
    for (account_number, solde), entry_number in zip(carried, entry_numbers, strict=True):
        acct = acct_map[account_number]
        is_debit = solde > 0
        abs_solde = abs(solde)
        db.add(
            AccountingEntry(
                entry_number=entry_number,
                date=ran_date,
                account_number=account_number,
                label=f"RAN {closed_fy.name} — {acct.label}",
                debit=abs_solde if is_debit else Decimal("0"),
                credit=Decimal("0") if is_debit else abs_solde,
                fiscal_year_id=new_fy.id,
                source_type=EntrySourceType.CLOTURE,
                source_id=closed_fy.id,
                group_key=build_entry_group_key(EntrySourceType.CLOTURE, closed_fy.id),
            )
        )

    await db.flush()
    await db.refresh(new_fy)
    return new_fy
