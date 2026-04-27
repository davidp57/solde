"""Accounting entry service — journal, balance, grand livre, compte de résultat."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import String, cast, func, literal_column, select
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


def _effective_gk_expr() -> ColumnElement[str]:
    """SQL expression mirroring _runtime_group_key priority:

    1. group_key if stored, else
    2. source_type || ':' || source_id (NULL when either column is NULL), else
    3. 'entry:' || id.
    """
    return func.coalesce(
        AccountingEntry.group_key,
        AccountingEntry.source_type.op("||")(
            literal_column("':'").op("||")(cast(AccountingEntry.source_id, String))
        ),
        literal_column("'entry:'").op("||")(cast(AccountingEntry.id, String)),
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
    limit: int | None = 100,
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
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def _query_group_keys_paged(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    account_number: str | None = None,
    source_type: EntrySourceType | None = None,
    fiscal_year_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[str]:
    """Return a paginated list of effective group keys matching the filter.

    The effective group key mirrors _runtime_group_key: group_key, then
    source_type:source_id, then entry:<id>.  Ordered by (MIN(date), MIN(id))
    so pagination is stable and chronological.
    """
    effective_gk = _effective_gk_expr().label("effective_gk")

    query = select(
        effective_gk,
        func.min(AccountingEntry.date).label("min_date"),
        func.min(AccountingEntry.id).label("min_id"),
    )
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
    query = (
        query.group_by(effective_gk)
        .order_by(
            func.min(AccountingEntry.date).asc(),
            func.min(AccountingEntry.id).asc(),
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return [row.effective_gk for row in result.all()]


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
        if entry.source_type in (EntrySourceType.INVOICE, EntrySourceType.WRITE_OFF)
        and entry.source_id is not None
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
        elif entry.source_type == EntrySourceType.WRITE_OFF and entry.source_id is not None:
            invoice = invoices_by_id.get(entry.source_id)
            if invoice is not None:
                source_reference = invoice.reference or invoice.number
                source_contact_name = _contact_display_name(contacts_by_id.get(invoice.contact_id))
                source_invoice_id = invoice.id
                source_invoice_type = _enum_value(invoice.type)
                source_invoice_number = invoice.number
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


async def get_journal(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    account_number: str | None = None,
    source_type: EntrySourceType | None = None,
    fiscal_year_id: int | None = None,
    skip: int = 0,
    limit: int | None = 100,
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
    # Step 1: paginate at the group level using SQL — avoid loading all entries.
    group_keys = await _query_group_keys_paged(
        db,
        from_date=from_date,
        to_date=to_date,
        account_number=account_number,
        source_type=source_type,
        fiscal_year_id=fiscal_year_id,
        skip=skip,
        limit=limit,
    )
    if not group_keys:
        return []

    # Step 2: load all entries belonging to those groups (all sibling lines).
    # Use the same effective_gk expression so entries whose group key is derived
    # from source_type:source_id (rather than a stored group_key) are also found.
    entries_q = (
        select(AccountingEntry)
        .where(_effective_gk_expr().in_(group_keys))
        .order_by(AccountingEntry.date.asc(), AccountingEntry.id.asc())
    )
    result = await db.execute(entries_q)
    group_entries = list(result.scalars().all())

    # Step 3: enrich and assemble groups in the SQL-paginated order.
    journal_lines = await _enrich_journal_entries(db, group_entries)
    lines_by_group: dict[str, list[AccountingEntryRead]] = {}
    for line in journal_lines:
        lines_by_group.setdefault(line.group_key, []).append(line)

    groups: list[AccountingEntryGroupRead] = []
    for group_key in group_keys:
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
    """Return balance grouped by account number using SQL aggregation."""
    query = select(
        AccountingEntry.account_number,
        func.sum(AccountingEntry.debit).label("total_debit"),
        func.sum(AccountingEntry.credit).label("total_credit"),
    )
    if from_date:
        query = query.where(AccountingEntry.date >= from_date)
    if to_date:
        query = query.where(AccountingEntry.date <= to_date)
    if fiscal_year_id:
        query = query.where(AccountingEntry.fiscal_year_id == fiscal_year_id)
    query = query.group_by(AccountingEntry.account_number).order_by(AccountingEntry.account_number)
    agg_result = await db.execute(query)
    agg_rows = agg_result.all()

    if not agg_rows:
        return []

    # Look up account labels and types in one query
    account_numbers = [row.account_number for row in agg_rows]
    acct_result = await db.execute(
        select(AccountingAccount).where(AccountingAccount.number.in_(account_numbers))
    )
    account_map = {a.number: a for a in acct_result.scalars().all()}

    rows: list[BalanceRow] = []
    for row in agg_rows:
        acct_obj = account_map.get(row.account_number)
        label = acct_obj.label if acct_obj else row.account_number
        acct_type = acct_obj.type if acct_obj else AccountType.ACTIF
        debit = Decimal(str(row.total_debit))
        credit = Decimal(str(row.total_credit))
        rows.append(
            BalanceRow(
                account_number=row.account_number,
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
        limit=None,
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
    """Return (total_charges, total_produits) for the given fiscal year using SQL aggregation."""
    query = (
        select(
            AccountingAccount.type,
            func.sum(AccountingEntry.debit).label("total_debit"),
            func.sum(AccountingEntry.credit).label("total_credit"),
        )
        .join(AccountingAccount, AccountingEntry.account_number == AccountingAccount.number)
        .where(AccountingAccount.type.in_([AccountType.CHARGE, AccountType.PRODUIT]))
    )
    if fiscal_year_id is not None:
        query = query.where(AccountingEntry.fiscal_year_id == fiscal_year_id)
    query = query.group_by(AccountingAccount.type)
    result = await db.execute(query)

    total_c = Decimal("0")
    total_p = Decimal("0")
    for row in result.all():
        debit = Decimal(str(row.total_debit))
        credit = Decimal(str(row.total_credit))
        if row.type == AccountType.CHARGE:
            total_c = debit - credit
        elif row.type == AccountType.PRODUIT:
            total_p = credit - debit
    return total_c, total_p


async def get_resultat(db: AsyncSession, fiscal_year_id: int | None = None) -> ResultatRead:
    """Build the compte de résultat for a given fiscal year using SQL aggregation."""
    query = (
        select(
            AccountingEntry.account_number,
            AccountingAccount.label,
            AccountingAccount.type,
            func.sum(AccountingEntry.debit).label("total_debit"),
            func.sum(AccountingEntry.credit).label("total_credit"),
        )
        .join(AccountingAccount, AccountingEntry.account_number == AccountingAccount.number)
        .where(AccountingAccount.type.in_([AccountType.CHARGE, AccountType.PRODUIT]))
    )
    if fiscal_year_id is not None:
        query = query.where(AccountingEntry.fiscal_year_id == fiscal_year_id)
    query = query.group_by(
        AccountingEntry.account_number,
        AccountingAccount.label,
        AccountingAccount.type,
    ).order_by(AccountingEntry.account_number)
    result = await db.execute(query)

    charges_rows: list[BalanceRow] = []
    produits_rows: list[BalanceRow] = []
    for row in result.all():
        debit = Decimal(str(row.total_debit))
        credit = Decimal(str(row.total_credit))
        if row.type == AccountType.CHARGE:
            tot = debit - credit
            charges_rows.append(
                BalanceRow(
                    account_number=row.account_number,
                    account_label=row.label,
                    account_type="charge",
                    total_debit=tot,
                    total_credit=Decimal("0"),
                    solde=tot,
                )
            )
        elif row.type == AccountType.PRODUIT:
            tot = credit - debit
            produits_rows.append(
                BalanceRow(
                    account_number=row.account_number,
                    account_label=row.label,
                    account_type="produit",
                    total_debit=Decimal("0"),
                    total_credit=tot,
                    solde=tot,
                )
            )

    total_c = sum((r.solde for r in charges_rows), Decimal("0"))
    total_p = sum((r.solde for r in produits_rows), Decimal("0"))

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
