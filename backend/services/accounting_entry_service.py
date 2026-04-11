"""Accounting entry service — journal, balance, grand livre, compte de résultat."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.schemas.accounting_entry import (
    BalanceRow,
    BilanRead,
    LedgerEntry,
    LedgerRead,
    ManualEntryCreate,
    ResultatRead,
)
from backend.services.accounting_engine import _next_entry_number

# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------


async def get_journal(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    account_number: str | None = None,
    source_type: EntrySourceType | None = None,
    fiscal_year_id: int | None = None,
    skip: int = 0,
    limit: int = 200,
) -> list[AccountingEntry]:
    query = select(AccountingEntry)
    if from_date:
        query = query.where(AccountingEntry.date >= from_date)
    if to_date:
        query = query.where(AccountingEntry.date <= to_date)
    if account_number:
        query = query.where(AccountingEntry.account_number == account_number)
    if source_type:
        query = query.where(AccountingEntry.source_type == source_type)
    if fiscal_year_id:
        query = query.where(AccountingEntry.fiscal_year_id == fiscal_year_id)
    query = query.order_by(AccountingEntry.date.asc(), AccountingEntry.id.asc())
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


async def get_balance(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    fiscal_year_id: int | None = None,
) -> list[BalanceRow]:
    """Return balance grouped by account number."""
    entries = await get_journal(
        db,
        from_date=from_date,
        to_date=to_date,
        fiscal_year_id=fiscal_year_id,
        limit=100_000,
    )

    # Aggregate per account
    totals: dict[str, dict[str, Decimal]] = {}
    for e in entries:
        acct = e.account_number
        if acct not in totals:
            totals[acct] = {"debit": Decimal("0"), "credit": Decimal("0")}
        totals[acct]["debit"] += Decimal(str(e.debit))
        totals[acct]["credit"] += Decimal(str(e.credit))

    # Look up account labels
    account_map: dict[str, AccountingAccount] = {}
    if totals:
        numbers = list(totals.keys())
        result = await db.execute(
            select(AccountingAccount).where(AccountingAccount.number.in_(numbers))
        )
        for account in result.scalars().all():
            account_map[account.number] = account

    rows: list[BalanceRow] = []
    for number, sums in sorted(totals.items()):
        acct_obj = account_map.get(number)
        label = acct_obj.label if acct_obj else number
        acct_type = acct_obj.type if acct_obj else "actif"
        debit = sums["debit"]
        credit = sums["credit"]
        rows.append(
            BalanceRow(
                account_number=number,
                account_label=label,
                account_type=acct_type,
                total_debit=debit,
                total_credit=credit,
                solde=debit - credit,
            )
        )

    return rows


# ---------------------------------------------------------------------------
# Grand livre (ledger)
# ---------------------------------------------------------------------------


async def get_ledger(
    db: AsyncSession,
    account_number: str,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    fiscal_year_id: int | None = None,
) -> LedgerRead:
    """Return all entries for a single account with a running balance."""
    entries = await get_journal(
        db,
        account_number=account_number,
        from_date=from_date,
        to_date=to_date,
        fiscal_year_id=fiscal_year_id,
        limit=100_000,
    )

    # Account label
    result = await db.execute(
        select(AccountingAccount).where(AccountingAccount.number == account_number)
    )
    acct_obj = result.scalar_one_or_none()
    label = acct_obj.label if acct_obj else account_number

    running = Decimal("0")
    ledger_entries: list[LedgerEntry] = []
    for e in entries:
        running += Decimal(str(e.debit)) - Decimal(str(e.credit))
        ledger_entries.append(
            LedgerEntry(
                id=e.id,
                entry_number=e.entry_number,
                date=e.date,
                label=e.label,
                debit=Decimal(str(e.debit)),
                credit=Decimal(str(e.credit)),
                running_balance=running,
            )
        )

    opening = Decimal("0")
    closing = running

    return LedgerRead(
        account_number=account_number,
        account_label=label,
        entries=ledger_entries,
        opening_balance=opening,
        closing_balance=closing,
    )


# ---------------------------------------------------------------------------
# Compte de résultat
# ---------------------------------------------------------------------------


async def _compute_resultat(
    db: AsyncSession, fiscal_year_id: int | None
) -> tuple[Decimal, Decimal]:
    """Return (total_charges, total_produits) for the given fiscal year."""
    entries = await get_journal(db, fiscal_year_id=fiscal_year_id, limit=100_000)

    # Get charge and produit account numbers
    result = await db.execute(
        select(AccountingAccount).where(
            AccountingAccount.type.in_([AccountType.CHARGE, AccountType.PRODUIT])
        )
    )
    acct_map: dict[str, AccountingAccount] = {a.number: a for a in result.scalars().all()}

    charges: dict[str, Decimal] = {}
    produits: dict[str, Decimal] = {}

    for e in entries:
        acct = acct_map.get(e.account_number)
        if acct is None:
            continue
        if acct.type == AccountType.CHARGE:
            charges[e.account_number] = (
                charges.get(e.account_number, Decimal("0"))
                + Decimal(str(e.debit))
                - Decimal(str(e.credit))
            )
        elif acct.type == AccountType.PRODUIT:
            produits[e.account_number] = (
                produits.get(e.account_number, Decimal("0"))
                + Decimal(str(e.credit))
                - Decimal(str(e.debit))
            )

    return sum(charges.values(), Decimal("0")), sum(produits.values(), Decimal("0"))


async def get_resultat(db: AsyncSession, fiscal_year_id: int | None = None) -> ResultatRead:
    """Build the compte de résultat for a given fiscal year."""
    entries = await get_journal(db, fiscal_year_id=fiscal_year_id, limit=100_000)

    result = await db.execute(
        select(AccountingAccount).where(
            AccountingAccount.type.in_([AccountType.CHARGE, AccountType.PRODUIT])
        )
    )
    acct_map: dict[str, AccountingAccount] = {a.number: a for a in result.scalars().all()}

    charge_totals: dict[str, Decimal] = {}
    produit_totals: dict[str, Decimal] = {}

    for e in entries:
        acct = acct_map.get(e.account_number)
        if acct is None:
            continue
        if acct.type == AccountType.CHARGE:
            charge_totals[e.account_number] = (
                charge_totals.get(e.account_number, Decimal("0"))
                + Decimal(str(e.debit))
                - Decimal(str(e.credit))
            )
        elif acct.type == AccountType.PRODUIT:
            produit_totals[e.account_number] = (
                produit_totals.get(e.account_number, Decimal("0"))
                + Decimal(str(e.credit))
                - Decimal(str(e.debit))
            )

    charges_rows = [
        BalanceRow(
            account_number=num,
            account_label=acct_map[num].label if num in acct_map else num,
            account_type="charge",
            total_debit=tot,
            total_credit=Decimal("0"),
            solde=tot,
        )
        for num, tot in sorted(charge_totals.items())
    ]
    produits_rows = [
        BalanceRow(
            account_number=num,
            account_label=acct_map[num].label if num in acct_map else num,
            account_type="produit",
            total_debit=Decimal("0"),
            total_credit=tot,
            solde=tot,
        )
        for num, tot in sorted(produit_totals.items())
    ]

    total_c = sum(charge_totals.values(), Decimal("0"))
    total_p = sum(produit_totals.values(), Decimal("0"))

    return ResultatRead(
        total_charges=total_c,
        total_produits=total_p,
        resultat=total_p - total_c,
        charges=charges_rows,
        produits=produits_rows,
    )


# ---------------------------------------------------------------------------
# Manual entry
# ---------------------------------------------------------------------------


async def create_manual_entry(
    db: AsyncSession, payload: ManualEntryCreate
) -> tuple[AccountingEntry, AccountingEntry]:
    """Create a balanced debit + credit entry pair."""
    debit_num = await _next_entry_number(db)

    debit_entry = AccountingEntry(
        entry_number=debit_num,
        date=payload.date,
        account_number=payload.debit_account,
        label=payload.label,
        debit=payload.amount,
        credit=Decimal("0"),
        fiscal_year_id=payload.fiscal_year_id,
        source_type=EntrySourceType.MANUAL,
        source_id=None,
    )
    db.add(debit_entry)
    await db.flush()  # ensure COUNT is updated before credit number generation

    credit_num = await _next_entry_number(db)
    credit_entry = AccountingEntry(
        entry_number=credit_num,
        date=payload.date,
        account_number=payload.credit_account,
        label=payload.label,
        debit=Decimal("0"),
        credit=payload.amount,
        fiscal_year_id=payload.fiscal_year_id,
        source_type=EntrySourceType.MANUAL,
        source_id=None,
    )
    db.add(debit_entry)
    db.add(credit_entry)
    await db.commit()
    await db.refresh(debit_entry)
    await db.refresh(credit_entry)
    return debit_entry, credit_entry


# ---------------------------------------------------------------------------
# Bilan simplifié (actif / passif)
# ---------------------------------------------------------------------------


async def get_bilan(db: AsyncSession, fiscal_year_id: int | None = None) -> BilanRead:
    """Build a simplified balance sheet grouping actif and passif accounts."""
    balance_rows = await get_balance(db, fiscal_year_id=fiscal_year_id)

    # Segregate by type
    actif_rows = [r for r in balance_rows if r.account_type == AccountType.ACTIF]
    passif_rows = [r for r in balance_rows if r.account_type == AccountType.PASSIF]

    # Compute current period resultat (produits - charges) to embed in passif
    total_c, total_p = await _compute_resultat(db, fiscal_year_id)
    resultat = total_p - total_c

    total_actif = sum((r.solde for r in actif_rows), Decimal("0"))
    total_passif = sum((r.solde for r in passif_rows), Decimal("0"))

    return BilanRead(
        actif=actif_rows,
        passif=passif_rows,
        total_actif=total_actif,
        total_passif=total_passif,
        resultat=resultat,
    )
