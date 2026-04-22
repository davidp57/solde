"""Accounting entry service — journal, balance, grand livre, compte de résultat."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_entry import (
    AccountingEntry,
    EntrySourceType,
    build_entry_group_key,
)
from backend.models.bank import BankTransaction, Deposit
from backend.models.contact import Contact
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.models.salary import Salary
from backend.schemas.accounting_entry import (
    AccountingEntryGroupRead,
    AccountingEntryRead,
    BalanceRow,
    BilanRead,
    LedgerEntry,
    LedgerRead,
    ManualEntryCreate,
    ManualEntryUpdate,
    ResultatRead,
)
from backend.services.accounting_engine import _next_entry_number

# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------


def _contact_display_name(contact: Contact | None) -> str | None:
    if contact is None:
        return None
    return f"{contact.prenom} {contact.nom}" if contact.prenom else contact.nom


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _runtime_group_key(entry: AccountingEntry) -> str:
    return (
        entry.group_key
        or build_entry_group_key(entry.source_type, entry.source_id)
        or f"entry:{entry.id}"
    )


def _ordered_unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _group_label(lines: list[AccountingEntryRead]) -> str:
    labels = _ordered_unique(line.label for line in lines if line.label)
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return " / ".join(labels)
    return f"{labels[0]} (+{len(labels) - 1})"


async def _query_journal_entries(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    account_number: str | None = None,
    source_type: EntrySourceType | None = None,
    fiscal_year_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
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
    query = query.offset(skip)
    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def _load_account_labels(
    db: AsyncSession, entries: Iterable[AccountingEntry]
) -> dict[str, str]:
    account_numbers = sorted({entry.account_number for entry in entries})
    if not account_numbers:
        return {}
    result = await db.execute(
        select(AccountingAccount).where(AccountingAccount.number.in_(account_numbers))
    )
    return {account.number: account.label for account in result.scalars().all()}


async def _enrich_journal_entries(
    db: AsyncSession,
    entries: list[AccountingEntry],
) -> list[AccountingEntryRead]:
    if not entries:
        return []

    account_labels = await _load_account_labels(db, entries)

    invoices_by_id: dict[int, Invoice] = {}
    payments_by_id: dict[int, Payment] = {}
    deposits_by_id: dict[int, Deposit] = {}
    bank_transactions_by_id: dict[int, BankTransaction] = {}
    salaries_by_id: dict[int, Salary] = {}

    invoice_source_ids = {
        entry.source_id
        for entry in entries
        if entry.source_type == EntrySourceType.INVOICE and entry.source_id is not None
    }
    payment_source_ids = {
        entry.source_id
        for entry in entries
        if entry.source_type == EntrySourceType.PAYMENT and entry.source_id is not None
    }
    deposit_source_ids = {
        entry.source_id
        for entry in entries
        if entry.source_type == EntrySourceType.DEPOSIT and entry.source_id is not None
    }
    salary_source_ids = {
        entry.source_id
        for entry in entries
        if entry.source_type == EntrySourceType.SALARY and entry.source_id is not None
    }
    gestion_source_ids = {
        entry.source_id
        for entry in entries
        if entry.source_type == EntrySourceType.GESTION and entry.source_id is not None
    }

    if invoice_source_ids:
        invoice_result = await db.execute(select(Invoice).where(Invoice.id.in_(invoice_source_ids)))
        invoices_by_id = {invoice.id: invoice for invoice in invoice_result.scalars().all()}

    if payment_source_ids:
        payment_result = await db.execute(select(Payment).where(Payment.id.in_(payment_source_ids)))
        payments_by_id = {payment.id: payment for payment in payment_result.scalars().all()}

    if deposit_source_ids:
        deposit_result = await db.execute(select(Deposit).where(Deposit.id.in_(deposit_source_ids)))
        deposits_by_id = {deposit.id: deposit for deposit in deposit_result.scalars().all()}

    if salary_source_ids:
        salary_result = await db.execute(select(Salary).where(Salary.id.in_(salary_source_ids)))
        salaries_by_id = {salary.id: salary for salary in salary_result.scalars().all()}

    if gestion_source_ids:
        bank_result = await db.execute(
            select(BankTransaction).where(BankTransaction.id.in_(gestion_source_ids))
        )
        bank_transactions_by_id = {
            bank_transaction.id: bank_transaction
            for bank_transaction in bank_result.scalars().all()
        }

    additional_invoice_ids = {payment.invoice_id for payment in payments_by_id.values()}
    if missing_invoice_ids := sorted(additional_invoice_ids.difference(invoices_by_id.keys())):
        invoice_result = await db.execute(
            select(Invoice).where(Invoice.id.in_(missing_invoice_ids))
        )
        invoices_by_id.update({invoice.id: invoice for invoice in invoice_result.scalars().all()})

    contact_ids = {
        contact_id
        for contact_id in {
            *(invoice.contact_id for invoice in invoices_by_id.values()),
            *(payment.contact_id for payment in payments_by_id.values()),
            *(salary.employee_id for salary in salaries_by_id.values()),
        }
        if contact_id is not None
    }
    contacts_by_id: dict[int, Contact] = {}
    if contact_ids:
        contact_result = await db.execute(
            select(Contact).where(Contact.id.in_(sorted(contact_ids)))
        )
        contacts_by_id = {contact.id: contact for contact in contact_result.scalars().all()}

    manual_entries_by_group: dict[str, list[AccountingEntry]] = {}
    for entry in entries:
        if entry.source_type == EntrySourceType.MANUAL:
            manual_entries_by_group.setdefault(_runtime_group_key(entry), []).append(entry)

    counterpart_by_id: dict[int, AccountingEntry] = {}
    for grouped_entries in manual_entries_by_group.values():
        if len(grouped_entries) != 2:
            continue
        first_entry, second_entry = grouped_entries
        counterpart_by_id[first_entry.id] = second_entry
        counterpart_by_id[second_entry.id] = first_entry

    journal_entries: list[AccountingEntryRead] = []
    for entry in entries:
        source_reference: str | None = None
        source_contact_name: str | None = None
        source_invoice_id: int | None = None
        source_invoice_type: str | None = None
        source_invoice_number: str | None = None

        if entry.source_type == EntrySourceType.INVOICE and entry.source_id is not None:
            invoice = invoices_by_id.get(entry.source_id)
            if invoice is not None:
                source_reference = invoice.reference or invoice.number
                source_contact_name = _contact_display_name(contacts_by_id.get(invoice.contact_id))
                source_invoice_id = invoice.id
                source_invoice_type = _enum_value(invoice.type)
                source_invoice_number = invoice.number
        elif entry.source_type == EntrySourceType.PAYMENT and entry.source_id is not None:
            payment = payments_by_id.get(entry.source_id)
            if payment is not None:
                invoice = invoices_by_id.get(payment.invoice_id)
                source_reference = (
                    payment.reference
                    or (invoice.reference if invoice is not None else None)
                    or (invoice.number if invoice is not None else None)
                )
                source_contact_name = _contact_display_name(
                    contacts_by_id.get(
                        invoice.contact_id if invoice is not None else payment.contact_id
                    )
                )
                if invoice is not None:
                    source_invoice_id = invoice.id
                    source_invoice_type = _enum_value(invoice.type)
                    source_invoice_number = invoice.number
        elif entry.source_type == EntrySourceType.DEPOSIT and entry.source_id is not None:
            deposit = deposits_by_id.get(entry.source_id)
            if deposit is not None:
                source_reference = (
                    deposit.bank_reference or f"{deposit.type} {deposit.date.isoformat()}"
                )
        elif entry.source_type == EntrySourceType.SALARY and entry.source_id is not None:
            salary = salaries_by_id.get(entry.source_id)
            if salary is not None:
                source_reference = salary.month
                source_contact_name = _contact_display_name(contacts_by_id.get(salary.employee_id))
        elif entry.source_type == EntrySourceType.GESTION and entry.source_id is not None:
            bank_transaction = bank_transactions_by_id.get(entry.source_id)
            if bank_transaction is not None:
                source_reference = bank_transaction.reference or bank_transaction.description

        counterpart_entry = counterpart_by_id.get(entry.id)
        journal_entries.append(
            AccountingEntryRead(
                id=entry.id,
                entry_number=entry.entry_number,
                group_key=_runtime_group_key(entry),
                date=entry.date,
                account_number=entry.account_number,
                account_label=account_labels.get(entry.account_number, entry.account_number),
                label=entry.label,
                debit=entry.debit,
                credit=entry.credit,
                fiscal_year_id=entry.fiscal_year_id,
                source_type=entry.source_type,
                source_id=entry.source_id,
                source_reference=source_reference,
                source_contact_name=source_contact_name,
                source_invoice_id=source_invoice_id,
                source_invoice_type=source_invoice_type,
                source_invoice_number=source_invoice_number,
                editable=entry.source_type == EntrySourceType.MANUAL
                and counterpart_entry is not None,
                counterpart_entry_id=counterpart_entry.id
                if counterpart_entry is not None
                else None,
                counterpart_account_number=(
                    counterpart_entry.account_number if counterpart_entry is not None else None
                ),
                counterpart_account_label=(
                    account_labels.get(
                        counterpart_entry.account_number,
                        counterpart_entry.account_number,
                    )
                    if counterpart_entry is not None
                    else None
                ),
            )
        )

    return journal_entries


async def _load_entries_for_groups(
    db: AsyncSession,
    matched_entries: list[AccountingEntry],
) -> list[AccountingEntry]:
    if not matched_entries:
        return []

    group_keys = sorted(
        {entry.group_key for entry in matched_entries if entry.group_key is not None}
    )
    source_groups = sorted(
        {
            (entry.source_type, entry.source_id)
            for entry in matched_entries
            if entry.group_key is None
            and entry.source_type is not None
            and entry.source_id is not None
        },
        key=lambda item: (str(item[0]), item[1]),
    )
    entry_ids = sorted(
        {
            entry.id
            for entry in matched_entries
            if entry.group_key is None and (entry.source_type is None or entry.source_id is None)
        }
    )

    conditions: list[ColumnElement[bool]] = []
    if group_keys:
        conditions.append(AccountingEntry.group_key.in_(group_keys))
    if source_groups:
        conditions.append(
            or_(
                *[
                    and_(
                        AccountingEntry.source_type == source_type,
                        AccountingEntry.source_id == source_id,
                    )
                    for source_type, source_id in source_groups
                ]
            )
        )
    if entry_ids:
        conditions.append(AccountingEntry.id.in_(entry_ids))

    if not conditions:
        return matched_entries

    query = (
        select(AccountingEntry)
        .where(or_(*conditions))
        .order_by(AccountingEntry.date.asc(), AccountingEntry.id.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_journal(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    account_number: str | None = None,
    source_type: EntrySourceType | None = None,
    fiscal_year_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AccountingEntryRead]:
    entries = await _query_journal_entries(
        db,
        from_date=from_date,
        to_date=to_date,
        account_number=account_number,
        source_type=source_type,
        fiscal_year_id=fiscal_year_id,
        skip=skip,
        limit=limit,
    )
    return await _enrich_journal_entries(db, entries)


async def get_grouped_journal(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    account_number: str | None = None,
    source_type: EntrySourceType | None = None,
    fiscal_year_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AccountingEntryGroupRead]:
    matched_entries = await _query_journal_entries(
        db,
        from_date=from_date,
        to_date=to_date,
        account_number=account_number,
        source_type=source_type,
        fiscal_year_id=fiscal_year_id,
        limit=100_000,
    )
    if not matched_entries:
        return []

    matched_group_keys = _ordered_unique(_runtime_group_key(entry) for entry in matched_entries)
    group_entries = await _load_entries_for_groups(db, matched_entries)
    journal_lines = await _enrich_journal_entries(db, group_entries)
    lines_by_group: dict[str, list[AccountingEntryRead]] = {}
    for line in journal_lines:
        lines_by_group.setdefault(line.group_key, []).append(line)

    groups: list[AccountingEntryGroupRead] = []
    for group_key in matched_group_keys:
        lines = lines_by_group.get(group_key, [])
        if not lines:
            continue
        lines.sort(key=lambda line: (line.date, line.id))
        first_line = lines[0]
        groups.append(
            AccountingEntryGroupRead(
                group_key=group_key,
                date=first_line.date,
                label=_group_label(lines),
                fiscal_year_id=first_line.fiscal_year_id,
                source_type=first_line.source_type,
                source_id=first_line.source_id,
                source_reference=first_line.source_reference,
                source_contact_name=first_line.source_contact_name,
                source_invoice_id=first_line.source_invoice_id,
                source_invoice_type=first_line.source_invoice_type,
                source_invoice_number=first_line.source_invoice_number,
                line_count=len(lines),
                total_debit=sum((line.debit for line in lines), Decimal("0")),
                total_credit=sum((line.credit for line in lines), Decimal("0")),
                account_numbers=_ordered_unique(line.account_number for line in lines),
                editable=any(line.editable for line in lines),
                lines=lines,
            )
        )

    if skip:
        groups = groups[skip:]
    groups = groups[:limit]
    return groups


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
    entries = await _query_journal_entries(
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
        totals[acct]["debit"] += e.debit
        totals[acct]["credit"] += e.credit

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
    opening = Decimal("0")
    if from_date is not None:
        opening_query = select(
            func.coalesce(func.sum(AccountingEntry.debit), 0),
            func.coalesce(func.sum(AccountingEntry.credit), 0),
        )
        opening_query = opening_query.where(AccountingEntry.account_number == account_number)
        opening_query = opening_query.where(AccountingEntry.date <= from_date - timedelta(days=1))
        if fiscal_year_id is not None:
            opening_query = opening_query.where(AccountingEntry.fiscal_year_id == fiscal_year_id)
        opening_result = await db.execute(opening_query)
        total_debit, total_credit = opening_result.one()
        opening = Decimal(str(total_debit)) - Decimal(str(total_credit))

    entries = await _query_journal_entries(
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

    running = opening
    ledger_entries: list[LedgerEntry] = []
    for e in entries:
        running += e.debit - e.credit
        ledger_entries.append(
            LedgerEntry(
                id=e.id,
                entry_number=e.entry_number,
                date=e.date,
                label=e.label,
                debit=e.debit,
                credit=e.credit,
                running_balance=running,
            )
        )
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
    entries = await _query_journal_entries(db, fiscal_year_id=fiscal_year_id, limit=100_000)

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
                charges.get(e.account_number, Decimal("0")) + e.debit - e.credit
            )
        elif acct.type == AccountType.PRODUIT:
            produits[e.account_number] = (
                produits.get(e.account_number, Decimal("0")) + e.credit - e.debit
            )

    return sum(charges.values(), Decimal("0")), sum(produits.values(), Decimal("0"))


async def get_resultat(db: AsyncSession, fiscal_year_id: int | None = None) -> ResultatRead:
    """Build the compte de résultat for a given fiscal year."""
    entries = await _query_journal_entries(db, fiscal_year_id=fiscal_year_id, limit=100_000)

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
                charge_totals.get(e.account_number, Decimal("0")) + e.debit - e.credit
            )
        elif acct.type == AccountType.PRODUIT:
            produit_totals[e.account_number] = (
                produit_totals.get(e.account_number, Decimal("0")) + e.credit - e.debit
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
    manual_group_id = debit_entry.id
    debit_entry.source_id = manual_group_id
    debit_entry.group_key = build_entry_group_key(EntrySourceType.MANUAL, manual_group_id)

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
        source_id=manual_group_id,
        group_key=build_entry_group_key(EntrySourceType.MANUAL, manual_group_id),
    )
    db.add(credit_entry)
    await db.commit()
    await db.refresh(debit_entry)
    await db.refresh(credit_entry)
    return debit_entry, credit_entry


async def update_manual_entry(
    db: AsyncSession,
    entry_id: int,
    payload: ManualEntryUpdate,
) -> tuple[AccountingEntry, AccountingEntry]:
    primary_entry = await db.get(AccountingEntry, entry_id)
    counterpart_entry = await db.get(AccountingEntry, payload.counterpart_entry_id)

    if primary_entry is None or counterpart_entry is None:
        raise ValueError("manual entry pair not found")
    if (
        primary_entry.source_type != EntrySourceType.MANUAL
        or counterpart_entry.source_type != EntrySourceType.MANUAL
    ):
        raise ValueError("only manual entries can be updated")
    if primary_entry.id == counterpart_entry.id:
        raise ValueError("manual entry pair must contain two distinct lines")

    debit_entry = primary_entry if primary_entry.debit > 0 else counterpart_entry
    credit_entry = counterpart_entry if debit_entry is primary_entry else primary_entry
    manual_group_id = (
        debit_entry.source_id or credit_entry.source_id or min(debit_entry.id, credit_entry.id)
    )
    group_key = build_entry_group_key(EntrySourceType.MANUAL, manual_group_id)

    debit_entry.date = payload.date
    debit_entry.account_number = payload.debit_account
    debit_entry.label = payload.label
    debit_entry.debit = payload.amount
    debit_entry.credit = Decimal("0")
    debit_entry.fiscal_year_id = payload.fiscal_year_id
    debit_entry.source_id = manual_group_id
    debit_entry.group_key = group_key

    credit_entry.date = payload.date
    credit_entry.account_number = payload.credit_account
    credit_entry.label = payload.label
    credit_entry.debit = Decimal("0")
    credit_entry.credit = payload.amount
    credit_entry.fiscal_year_id = payload.fiscal_year_id
    credit_entry.source_id = manual_group_id
    credit_entry.group_key = group_key

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
