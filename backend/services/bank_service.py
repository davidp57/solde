"""Bank service — transactions, deposit slips and reconciliation."""

from __future__ import annotations

import json
from calendar import monthrange
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Protocol

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry
from backend.models.bank import (
    BankAccountType,
    BankTransaction,
    BankTransactionCategory,
    BankTransactionSource,
    Deposit,
    DepositType,
    bank_transaction_payments,
    deposit_payments,
)
from backend.models.cash import CashEntrySource, CashMovementType
from backend.models.invoice import Invoice, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.bank import (
    BankTransactionClientPaymentsCreate,
    BankTransactionCreate,
    BankTransactionUpdate,
    DepositCreate,
    DepositUpdate,
)
from backend.services import payment as payment_service
from backend.services.bank_import import detect_transaction_category


class _Reconcilable(Protocol):
    """Minimal protocol for objects that carry a payment id for reconciliation links."""

    id: int


_CURRENT_ACCOUNT_NUMBER = "512100"
_SAVINGS_ACCOUNT_NUMBER = "512102"
_FISCAL_YEAR_OPENING_LABEL_PREFIX = "Ouverture de l'exercice comptable"


def _shift_month(value: date, months: int) -> date:
    year = value.year
    month = value.month + months
    while month <= 0:
        year -= 1
        month += 12
    while month > 12:
        year += 1
        month -= 12
    return date(year, month, 1)


def _month_windows(months: int) -> list[tuple[str, date]]:
    today = date.today()
    current_month = today.replace(day=1)
    first_month = _shift_month(current_month, -(months - 1))
    windows: list[tuple[str, date]] = []
    month_cursor = first_month
    while month_cursor <= current_month:
        month_end = month_cursor.replace(day=monthrange(month_cursor.year, month_cursor.month)[1])
        windows.append(
            (
                month_cursor.strftime("%Y-%m"),
                today if month_cursor == current_month else month_end,
            )
        )
        month_cursor = _shift_month(month_cursor, 1)
    return windows


def _is_fiscal_year_opening_label(label: str) -> bool:
    return label.startswith(_FISCAL_YEAR_OPENING_LABEL_PREFIX)


def _require_transaction_direction(
    tx: BankTransaction,
    *,
    positive: bool,
    purpose: str,
) -> None:
    if positive and tx.amount <= 0:
        raise ValueError(f"only positive bank transactions can {purpose}")
    if not positive and tx.amount >= 0:
        raise ValueError(f"only negative bank transactions can {purpose}")


async def _require_unreconciled_transaction(
    db: AsyncSession,
    tx: BankTransaction,
) -> None:
    if tx.reconciled or tx.payment_id is not None:
        raise ValueError("bank transaction is already reconciled")
    linked_result = await db.execute(
        select(bank_transaction_payments.c.transaction_id).where(
            bank_transaction_payments.c.transaction_id == tx.id
        )
    )
    if linked_result.scalar_one_or_none() is not None:
        raise ValueError("bank transaction is already reconciled")


async def _require_linkable_payment(
    db: AsyncSession,
    *,
    payment_id: int,
    invoice_type: InvoiceType,
) -> Payment:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise LookupError("Payment not found")
    if payment.method != PaymentMethod.VIREMENT:
        invoice_kind = "client" if invoice_type == InvoiceType.CLIENT else "supplier"
        raise ValueError(f"only existing {invoice_kind} virement payments can be linked")
    inv_result = await db.execute(select(Invoice.type).where(Invoice.id == payment.invoice_id))
    actual_type = inv_result.scalar_one_or_none()
    if actual_type != invoice_type:
        invoice_kind = "client" if invoice_type == InvoiceType.CLIENT else "supplier"
        raise ValueError(f"only existing {invoice_kind} virement payments can be linked")

    linked_payment_result = await db.execute(
        select(bank_transaction_payments.c.transaction_id).where(
            bank_transaction_payments.c.payment_id == payment.id
        )
    )
    if linked_payment_result.scalar_one_or_none() is not None:
        raise ValueError("payment is already linked to another bank transaction")
    legacy_linked_payment_result = await db.execute(
        select(BankTransaction.id).where(BankTransaction.payment_id == payment.id)
    )
    if legacy_linked_payment_result.scalar_one_or_none() is not None:
        raise ValueError("payment is already linked to another bank transaction")
    return payment


def _build_reconciled_with_value(
    payment_ids: Sequence[int], invoice_numbers: dict[int, str | None]
) -> str | None:
    if not payment_ids:
        return None
    if len(payment_ids) == 1:
        return invoice_numbers.get(payment_ids[0])
    first_label = invoice_numbers.get(payment_ids[0]) or f"payment-{payment_ids[0]}"
    return f"{first_label} +{len(payment_ids) - 1}"


async def _store_transaction_payment_links(
    db: AsyncSession,
    *,
    tx: BankTransaction,
    payments: Sequence[_Reconcilable],
) -> None:
    payment_ids = [p.id for p in payments]
    await db.execute(
        insert(bank_transaction_payments),
        [{"transaction_id": tx.id, "payment_id": pid} for pid in payment_ids],
    )
    # Fetch invoice numbers for the reconciled_with label
    inv_rows = await db.execute(
        select(Payment.id, Invoice.number)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .where(Payment.id.in_(payment_ids))
    )
    invoice_numbers: dict[int, str | None] = {row[0]: row[1] for row in inv_rows}
    tx.reconciled = True
    tx.reconciled_with = _build_reconciled_with_value(payment_ids, invoice_numbers)
    tx.payment_id = payment_ids[0] if len(payment_ids) == 1 else None


async def _finalize_payment_link(
    db: AsyncSession,
    *,
    tx: BankTransaction,
    payment: Payment,
    expected_amount: Decimal,
) -> BankTransaction:
    return await _finalize_payment_links(
        db,
        tx=tx,
        payments=[payment],
        expected_amount=expected_amount,
        error_message="bank transaction amount must match payment amount",
    )


async def _finalize_payment_links(
    db: AsyncSession,
    *,
    tx: BankTransaction,
    payments: list[Payment],
    expected_amount: Decimal,
    error_message: str,
) -> BankTransaction:
    payments_total = sum((payment.amount for payment in payments), start=Decimal("0"))
    if payments_total != expected_amount:
        raise ValueError(error_message)

    for payment in payments:
        payment.deposited = True
        payment.deposit_date = tx.date

    await _store_transaction_payment_links(db, tx=tx, payments=payments)
    await db.flush()
    await db.flush()
    await db.refresh(tx)
    return tx


async def _current_bank_balance(db: AsyncSession) -> Decimal:
    """Return the sum of all bank transaction amounts for the courant account."""
    result = await db.execute(
        select(func.sum(BankTransaction.amount)).where(
            BankTransaction.bank_account == BankAccountType.COURANT
        )
    )
    total = result.scalar_one_or_none() or Decimal("0")
    return Decimal(str(total))


async def _savings_bank_balance(db: AsyncSession) -> Decimal:
    """Return the sum of all bank transaction amounts for the epargne account."""
    result = await db.execute(
        select(func.sum(BankTransaction.amount)).where(
            BankTransaction.bank_account == BankAccountType.EPARGNE
        )
    )
    total = result.scalar_one_or_none() or Decimal("0")
    return Decimal(str(total))


async def recompute_bank_balances(db: AsyncSession) -> bool:
    """Recompute running bank balances per account and report whether persisted values changed."""
    # Process each account independently to maintain correct per-account running totals
    running_balances: dict[BankAccountType, Decimal] = {
        BankAccountType.COURANT: Decimal("0"),
        BankAccountType.EPARGNE: Decimal("0"),
    }
    result = await db.execute(
        select(BankTransaction).order_by(BankTransaction.date.asc(), BankTransaction.id.asc())
    )
    changed = False
    for entry in result.scalars().all():
        acct = entry.bank_account
        running_balances[acct] += entry.amount
        if entry.balance_after != running_balances[acct]:
            entry.balance_after = running_balances[acct]
            changed = True
    return changed


async def get_excel_cutoffs(db: AsyncSession) -> dict[BankAccountType, date]:
    """Return the max date of Excel-imported transactions per bank account.

    Used as a cut-off when importing OFX/CSV/QIF files to avoid re-importing
    transactions that were already captured through the Excel import.
    """
    result = await db.execute(
        select(BankTransaction.bank_account, func.max(BankTransaction.date))
        .where(
            BankTransaction.source.in_(
                [
                    BankTransactionSource.IMPORT_EXCEL,
                    BankTransactionSource.IMPORT,  # legacy: Excel imports before source enum
                ]
            )
        )
        .group_by(BankTransaction.bank_account)
    )
    return {row[0]: row[1] for row in result.all()}


async def add_transaction(
    db: AsyncSession, payload: BankTransactionCreate
) -> BankTransaction | None:
    """Insert a transaction. Returns None (skipped) if the reference already exists."""
    if payload.reference:
        existing = await db.execute(
            select(BankTransaction).where(BankTransaction.reference == payload.reference)
        )
        if existing.scalar_one_or_none() is not None:
            return None
    tx = await create_bank_transaction_record(
        db,
        date=payload.date,
        amount=payload.amount,
        reference=payload.reference,
        description=payload.description,
        source=payload.source,
        bank_account=payload.bank_account,
    )
    await db.flush()
    await db.refresh(tx)
    return tx


async def create_bank_transaction_record(
    db: AsyncSession,
    *,
    date: date,
    amount: Decimal,
    reference: str | None = None,
    description: str = "",
    source: BankTransactionSource = BankTransactionSource.MANUAL,
    bank_account: BankAccountType = BankAccountType.COURANT,
) -> BankTransaction:
    """Create a bank transaction without committing, then recompute balances."""
    tx = BankTransaction(
        date=date,
        amount=amount,
        reference=reference,
        description=description,
        balance_after=Decimal("0"),
        source=source,
        bank_account=bank_account,
        detected_category=(
            BankTransactionCategory.UNCATEGORIZED
            if source == BankTransactionSource.SYSTEM_OPENING
            else detect_transaction_category(
                amount=amount,
                description=description,
                reference=reference,
            )
        ),
    )
    db.add(tx)
    await db.flush()
    await recompute_bank_balances(db)
    return tx


async def get_transaction(db: AsyncSession, tx_id: int) -> BankTransaction | None:
    result = await db.execute(select(BankTransaction).where(BankTransaction.id == tx_id))
    return result.scalar_one_or_none()


async def list_transactions(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    unreconciled_only: bool = False,
    bank_account: BankAccountType | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[BankTransaction]:
    query = select(BankTransaction)
    if from_date is not None:
        query = query.where(BankTransaction.date >= from_date)
    if to_date is not None:
        query = query.where(BankTransaction.date <= to_date)
    if unreconciled_only:
        query = query.where(BankTransaction.reconciled == False)  # noqa: E712
    if bank_account is not None:
        query = query.where(BankTransaction.bank_account == bank_account)
    query = query.order_by(BankTransaction.date.desc(), BankTransaction.id.desc())
    query = query.offset(skip)
    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_transactions(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    unreconciled_only: bool = False,
    bank_account: BankAccountType | None = None,
) -> int:
    """Count bank transactions matching filters (no limit)."""
    query = select(func.count()).select_from(BankTransaction)
    if from_date is not None:
        query = query.where(BankTransaction.date >= from_date)
    if to_date is not None:
        query = query.where(BankTransaction.date <= to_date)
    if unreconciled_only:
        query = query.where(BankTransaction.reconciled == False)  # noqa: E712
    if bank_account is not None:
        query = query.where(BankTransaction.bank_account == bank_account)
    result = await db.execute(query)
    return result.scalar_one()


async def get_monthly_funds_series(
    db: AsyncSession,
    *,
    months: int = 6,
) -> list[dict[str, Decimal | str]]:
    if await recompute_bank_balances(db):
        await db.flush()

    result = await db.execute(
        select(BankTransaction.date, BankTransaction.balance_after)
        .where(BankTransaction.bank_account == BankAccountType.COURANT)
        .order_by(BankTransaction.date.asc(), BankTransaction.id.asc())
    )
    current_account_points = [
        (point_date, Decimal(str(balance_after))) for point_date, balance_after in result.all()
    ]

    windows = _month_windows(months)
    max_period_end = windows[-1][1] if windows else date.today()

    accounting_result = await db.execute(
        select(
            AccountingEntry.date,
            AccountingEntry.account_number,
            AccountingEntry.label,
            AccountingEntry.debit,
            AccountingEntry.credit,
        )
        .where(
            AccountingEntry.account_number.in_([_CURRENT_ACCOUNT_NUMBER, _SAVINGS_ACCOUNT_NUMBER]),
            AccountingEntry.date <= max_period_end,
        )
        .order_by(AccountingEntry.date.asc(), AccountingEntry.id.asc())
    )
    accounting_points = [
        (
            point_date,
            account_number,
            label,
            Decimal(str(debit)) - Decimal(str(credit)),
        )
        for point_date, account_number, label, debit, credit in accounting_result.all()
    ]

    rows: list[dict[str, Decimal | str]] = []
    transaction_current_balance = Decimal("0")
    accounting_balances = {
        _CURRENT_ACCOUNT_NUMBER: Decimal("0"),
        _SAVINGS_ACCOUNT_NUMBER: Decimal("0"),
    }
    current_point_index = 0
    accounting_point_index = 0
    for month_label, period_end in windows:
        while (
            current_point_index < len(current_account_points)
            and current_account_points[current_point_index][0] <= period_end
        ):
            transaction_current_balance = current_account_points[current_point_index][1]
            current_point_index += 1
        while (
            accounting_point_index < len(accounting_points)
            and accounting_points[accounting_point_index][0] <= period_end
        ):
            _, account_number, label, amount_delta = accounting_points[accounting_point_index]
            if _is_fiscal_year_opening_label(label):
                accounting_balances[account_number] = amount_delta
            else:
                accounting_balances[account_number] += amount_delta
            accounting_point_index += 1
        accounting_current_balance = accounting_balances[_CURRENT_ACCOUNT_NUMBER]
        savings_account_balance = accounting_balances[_SAVINGS_ACCOUNT_NUMBER]
        current_account_balance = (
            transaction_current_balance if current_point_index > 0 else accounting_current_balance
        )
        total_balance = current_account_balance + savings_account_balance
        rows.append(
            {
                "month": month_label,
                "current_account": current_account_balance,
                "savings_account": savings_account_balance,
                "total": total_balance,
                "balance": total_balance,
            }
        )
    return rows


async def update_transaction(
    db: AsyncSession, tx: BankTransaction, payload: BankTransactionUpdate
) -> BankTransaction:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
    await db.flush()
    await recompute_bank_balances(db)
    await db.flush()
    await db.refresh(tx)
    return tx


async def delete_manual_transaction(db: AsyncSession, tx: BankTransaction) -> None:
    """Delete a manual (or system_opening) transaction and recompute balances.

    Raises ValueError if the transaction has a non-manual source or is reconciled.
    """
    if tx.source not in (
        BankTransactionSource.MANUAL,
        BankTransactionSource.SYSTEM_OPENING,
    ):
        raise ValueError("Only manual transactions can be deleted")
    if tx.reconciled:
        raise ValueError("Reconciled transactions cannot be deleted")
    await db.delete(tx)
    await db.flush()
    await recompute_bank_balances(db)
    await db.flush()


async def reconcile_transactions_bulk(
    db: AsyncSession,
    *,
    ids: list[int],
) -> int:
    """Mark a batch of transactions as reconciled and generate accounting entries.

    Returns the count of updated rows.
    """
    from backend.services import accounting_engine  # noqa: PLC0415

    result = await db.execute(
        select(BankTransaction)
        .where(BankTransaction.id.in_(ids))
        .where(BankTransaction.reconciled.is_(False))
    )
    txs = result.scalars().all()

    for tx in txs:
        tx.reconciled = True
        await accounting_engine.generate_entries_for_bank_transaction(db, tx)

    await db.flush()
    return len(txs)


async def create_client_payment_from_transaction(
    db: AsyncSession,
    *,
    tx_id: int,
    invoice_id: int,
) -> BankTransaction:
    """Create a client virement from a positive bank transaction and reconcile it."""
    tx = await get_transaction(db, tx_id)
    if tx is None:
        raise LookupError("Transaction not found")
    _require_transaction_direction(tx, positive=True, purpose="create client payments")
    await _require_unreconciled_transaction(db, tx)

    payment = await payment_service.create_bank_reconciled_client_payment(
        db,
        invoice_id=invoice_id,
        amount=tx.amount,
        payment_date=tx.date,
        reference=tx.description or None,
        notes=tx.description or None,
    )

    await _store_transaction_payment_links(db, tx=tx, payments=[payment])
    await db.flush()
    await db.flush()
    await db.refresh(tx)
    return tx


async def create_client_payments_from_transaction(
    db: AsyncSession,
    *,
    tx_id: int,
    payload: BankTransactionClientPaymentsCreate,
) -> BankTransaction:
    """Create multiple client virements from a single positive bank transaction."""
    tx = await get_transaction(db, tx_id)
    if tx is None:
        raise LookupError("Transaction not found")
    _require_transaction_direction(tx, positive=True, purpose="create client payments")
    await _require_unreconciled_transaction(db, tx)

    expected_amount = tx.amount
    allocated_amount = sum(
        (allocation.amount for allocation in payload.allocations),
        start=Decimal("0"),
    )
    if allocated_amount != expected_amount:
        raise ValueError("allocated amount must match bank transaction amount")

    payments: list[_Reconcilable] = []
    for allocation in payload.allocations:
        payment = await payment_service.create_bank_reconciled_client_payment(
            db,
            invoice_id=allocation.invoice_id,
            amount=allocation.amount,
            payment_date=tx.date,
            reference=tx.description or None,
            notes=tx.description or None,
            flush_and_refresh=False,
        )
        payments.append(payment)

    await _store_transaction_payment_links(db, tx=tx, payments=payments)
    await db.flush()
    await db.flush()
    await db.refresh(tx)
    return tx


async def create_supplier_payment_from_transaction(
    db: AsyncSession,
    *,
    tx_id: int,
    invoice_id: int,
) -> BankTransaction:
    """Create a supplier virement from a negative bank transaction and reconcile it."""
    tx = await get_transaction(db, tx_id)
    if tx is None:
        raise LookupError("Transaction not found")
    _require_transaction_direction(tx, positive=False, purpose="create supplier payments")
    await _require_unreconciled_transaction(db, tx)

    payment = await payment_service.create_bank_reconciled_supplier_payment(
        db,
        invoice_id=invoice_id,
        amount=abs(tx.amount),
        payment_date=tx.date,
        reference=tx.description or None,
        notes=tx.description or None,
    )

    await _store_transaction_payment_links(db, tx=tx, payments=[payment])
    await db.flush()
    await db.flush()
    await db.refresh(tx)
    return tx


async def link_client_payment_to_transaction(
    db: AsyncSession,
    *,
    tx_id: int,
    payment_id: int,
) -> BankTransaction:
    """Link a positive bank transaction to an existing client virement payment."""
    tx = await get_transaction(db, tx_id)
    if tx is None:
        raise LookupError("Transaction not found")
    _require_transaction_direction(
        tx,
        positive=True,
        purpose="link existing client payments",
    )
    await _require_unreconciled_transaction(db, tx)

    payment = await _require_linkable_payment(
        db,
        payment_id=payment_id,
        invoice_type=InvoiceType.CLIENT,
    )
    return await _finalize_payment_link(
        db,
        tx=tx,
        payment=payment,
        expected_amount=tx.amount,
    )


async def link_client_payments_to_transaction(
    db: AsyncSession,
    *,
    tx_id: int,
    payment_ids: list[int],
) -> BankTransaction:
    """Link a positive bank transaction to multiple existing client virement payments."""
    tx = await get_transaction(db, tx_id)
    if tx is None:
        raise LookupError("Transaction not found")
    _require_transaction_direction(
        tx,
        positive=True,
        purpose="link existing client payments",
    )
    await _require_unreconciled_transaction(db, tx)

    payments: list[Payment] = []
    for payment_id in payment_ids:
        payment = await _require_linkable_payment(
            db,
            payment_id=payment_id,
            invoice_type=InvoiceType.CLIENT,
        )
        payments.append(payment)

    return await _finalize_payment_links(
        db,
        tx=tx,
        payments=payments,
        expected_amount=tx.amount,
        error_message="linked payments total must match bank transaction amount",
    )


async def link_supplier_payment_to_transaction(
    db: AsyncSession,
    *,
    tx_id: int,
    payment_id: int,
) -> BankTransaction:
    """Link a negative bank transaction to an existing supplier virement payment."""
    tx = await get_transaction(db, tx_id)
    if tx is None:
        raise LookupError("Transaction not found")
    _require_transaction_direction(
        tx,
        positive=False,
        purpose="link existing supplier payments",
    )
    await _require_unreconciled_transaction(db, tx)

    payment = await _require_linkable_payment(
        db,
        payment_id=payment_id,
        invoice_type=InvoiceType.FOURNISSEUR,
    )
    return await _finalize_payment_link(
        db,
        tx=tx,
        payment=payment,
        expected_amount=abs(tx.amount),
    )


async def get_bank_balance(db: AsyncSession) -> dict[str, Decimal]:
    courant = await _current_bank_balance(db)
    epargne = await _savings_bank_balance(db)
    return {"balance": courant, "balance_courant": courant, "balance_epargne": epargne}


# ---------------------------------------------------------------------------
# Deposit slips
# ---------------------------------------------------------------------------


async def create_deposit(db: AsyncSession, payload: DepositCreate) -> Deposit:
    """Create a deposit slip.

    Cheques deposit: payment_ids must be provided; amounts are summed from those
    payments, which are marked as ``in_deposit=True`` (en transit — assigned to
    a slip but not yet confirmed at the bank).  ``deposited`` is only set to
    ``True`` at confirmation time.  Accounting entries are generated on
    *confirmation* (when the slip is physically taken to the bank).

    Especes deposit: total_amount is provided directly (the cash was already
    counted from the till).  No payment links, no CashEntry, no accounting
    entries at this stage — all that happens on *confirmation*.
    """
    if payload.type == DepositType.CHEQUES:
        if not payload.payment_ids:
            raise ValueError("at least one payment_id is required for a cheques deposit")

        result = await db.execute(select(Payment).where(Payment.id.in_(payload.payment_ids)))
        payments = list(result.scalars().all())
        if len(payments) != len(payload.payment_ids):
            raise ValueError("one or more payment_ids not found")

        invalid_payment = next(
            (p for p in payments if p.method != PaymentMethod.CHEQUE),
            None,
        )
        if invalid_payment is not None:
            raise ValueError("all payments in a cheques deposit must be cheque payments")

        already_busy = [p for p in payments if p.deposited or p.in_deposit]
        if already_busy:
            ids = [p.id for p in already_busy]
            raise ValueError(
                f"payments {ids} are already deposited or assigned to another deposit slip"
            )

        total_amount = sum((p.amount for p in payments), Decimal("0"))

        deposit = Deposit(
            date=payload.date,
            type=payload.type,
            total_amount=total_amount,
            bank_reference=payload.bank_reference,
            notes=payload.notes,
            denomination_details=None,
        )
        db.add(deposit)
        await db.flush()

        await db.execute(
            insert(deposit_payments),
            [{"deposit_id": deposit.id, "payment_id": pid} for pid in payload.payment_ids],
        )

        # Mark cheques as "en transit" — assigned to a slip, not yet confirmed
        for p in payments:
            p.in_deposit = True
            p.deposit_date = payload.date

    else:
        # DepositType.ESPECES
        if payload.total_amount is None or payload.total_amount <= Decimal("0"):
            raise ValueError("total_amount must be a positive amount for an especes deposit")
        if payload.payment_ids:
            raise ValueError("payment_ids must be empty for an especes deposit")

        deposit = Deposit(
            date=payload.date,
            type=payload.type,
            total_amount=payload.total_amount,
            bank_reference=payload.bank_reference,
            notes=payload.notes,
            denomination_details=payload.denomination_details,
        )
        db.add(deposit)
        await db.flush()

    await db.flush()
    await db.refresh(deposit)
    return deposit


async def update_deposit(db: AsyncSession, deposit_id: int, payload: DepositUpdate) -> Deposit:
    """Update an unconfirmed deposit slip (modify payment selection or amount).

    Cheques deposit: ``payment_ids`` replaces the current selection.  The set
    must remain non-empty and all entries must be cheque payments that are not
    already assigned to another slip.
    Especes deposit: ``total_amount`` and/or ``denomination_details`` can be
    updated independently.
    """
    deposit = await get_deposit(db, deposit_id)
    if deposit is None:
        raise LookupError("Deposit not found")
    if deposit.confirmed:
        raise ValueError("Cannot update a confirmed deposit")

    if deposit.type == DepositType.CHEQUES:
        if payload.payment_ids is not None:
            new_ids = payload.payment_ids
            if not new_ids:
                raise ValueError("A cheques deposit must include at least one payment")

            current_pids = await get_deposit_payment_ids(db, deposit_id)
            current_set = set(current_pids)
            new_set = set(new_ids)

            # Validate new payments
            if new_set:
                result = await db.execute(select(Payment).where(Payment.id.in_(new_set)))
                new_payments = list(result.scalars().all())
                if len(new_payments) != len(new_set):
                    raise ValueError("one or more payment_ids not found")
                invalid = next((p for p in new_payments if p.method != PaymentMethod.CHEQUE), None)
                if invalid:
                    raise ValueError("all payments in a cheques deposit must be cheque payments")
                # Check that payments not already in THIS deposit aren't busy elsewhere
                busy = [
                    p
                    for p in new_payments
                    if p.id not in current_set and (p.deposited or p.in_deposit)
                ]
                if busy:
                    raise ValueError(
                        f"payments {[p.id for p in busy]} are already assigned to another deposit"
                    )

            # Remove payments no longer selected
            to_remove = current_set - new_set
            if to_remove:
                await db.execute(
                    delete(deposit_payments).where(
                        deposit_payments.c.deposit_id == deposit_id,
                        deposit_payments.c.payment_id.in_(to_remove),
                    )
                )
                rm_result = await db.execute(select(Payment).where(Payment.id.in_(to_remove)))
                for p in rm_result.scalars().all():
                    p.in_deposit = False
                    p.deposit_date = None
                await db.flush()

            # Add newly selected payments
            to_add = new_set - current_set
            if to_add:
                add_result = await db.execute(select(Payment).where(Payment.id.in_(to_add)))
                for p in add_result.scalars().all():
                    p.in_deposit = True
                    p.deposit_date = deposit.date
                await db.execute(
                    insert(deposit_payments),
                    [{"deposit_id": deposit_id, "payment_id": pid} for pid in to_add],
                )
                await db.flush()

            # Recompute total_amount from the final set
            all_pids = new_set
            if all_pids:
                total_result = await db.execute(select(Payment).where(Payment.id.in_(all_pids)))
                deposit.total_amount = sum(
                    (p.amount for p in total_result.scalars().all()), Decimal("0")
                )

    else:
        # DepositType.ESPECES
        if payload.denomination_details is not None:
            deposit.denomination_details = payload.denomination_details
            # Recompute total from denominations; ignore any client-supplied total_amount
            try:
                lines = json.loads(payload.denomination_details)
                deposit.total_amount = sum(
                    (
                        Decimal(str(line["value"])) * int(line["count"])
                        for line in lines
                        if line.get("count", 0)
                    ),
                    Decimal("0"),
                )
            except Exception as exc:
                raise ValueError("invalid denomination_details format") from exc
        elif payload.total_amount is not None:
            if payload.total_amount <= Decimal("0"):
                raise ValueError("total_amount must be a positive amount")
            deposit.total_amount = payload.total_amount

    await db.flush()
    await db.refresh(deposit)
    return deposit


async def delete_deposit(db: AsyncSession, deposit_id: int) -> None:
    """Cancel and delete an unconfirmed deposit slip.

    For cheques deposits, all linked payments are freed (``in_deposit`` reset
    to ``False``) so they can be included in a new slip.
    """
    deposit = await get_deposit(db, deposit_id)
    if deposit is None:
        raise LookupError("Deposit not found")
    if deposit.confirmed:
        raise ValueError("Cannot cancel a confirmed deposit")

    if deposit.type == DepositType.CHEQUES:
        pids = await get_deposit_payment_ids(db, deposit_id)
        if pids:
            result = await db.execute(select(Payment).where(Payment.id.in_(pids)))
            for p in result.scalars().all():
                p.in_deposit = False
                p.deposit_date = None
            await db.flush()

    # Always clean up the association rows (prevents FK constraint errors)
    await db.execute(delete(deposit_payments).where(deposit_payments.c.deposit_id == deposit_id))
    await db.flush()
    await db.delete(deposit)
    await db.flush()


async def get_transaction_payment_ids(db: AsyncSession, tx_id: int) -> list[int]:
    return (await get_transaction_payment_ids_map(db, [tx_id])).get(tx_id, [])


async def get_transaction_payment_ids_map(
    db: AsyncSession,
    tx_ids: list[int],
) -> dict[int, list[int]]:
    if not tx_ids:
        return {}

    payment_ids_by_tx_id: dict[int, list[int]] = {tx_id: [] for tx_id in tx_ids}

    association_result = await db.execute(
        select(
            bank_transaction_payments.c.transaction_id,
            bank_transaction_payments.c.payment_id,
        )
        .where(bank_transaction_payments.c.transaction_id.in_(tx_ids))
        .order_by(
            bank_transaction_payments.c.transaction_id.asc(),
            bank_transaction_payments.c.payment_id.asc(),
        )
    )
    for transaction_id, payment_id in association_result.all():
        payment_ids_by_tx_id[transaction_id].append(payment_id)

    legacy_result = await db.execute(
        select(BankTransaction.id, BankTransaction.payment_id).where(
            BankTransaction.id.in_(tx_ids),
            BankTransaction.payment_id.is_not(None),
        )
    )
    for transaction_id, payment_id in legacy_result.all():
        if payment_id is not None and not payment_ids_by_tx_id[transaction_id]:
            payment_ids_by_tx_id[transaction_id] = [payment_id]

    return payment_ids_by_tx_id


async def get_deposit(db: AsyncSession, deposit_id: int) -> Deposit | None:
    result = await db.execute(select(Deposit).where(Deposit.id == deposit_id))
    return result.scalar_one_or_none()


async def list_deposits(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    confirmed: bool | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Deposit]:
    query = select(Deposit)
    if from_date is not None:
        query = query.where(Deposit.date >= from_date)
    if to_date is not None:
        query = query.where(Deposit.date <= to_date)
    if confirmed is not None:
        query = query.where(Deposit.confirmed == confirmed)
    query = query.order_by(Deposit.date.desc(), Deposit.id.desc()).offset(skip)
    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_deposits(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    confirmed: bool | None = None,
) -> int:
    """Count deposits matching filters (no limit)."""
    query = select(func.count()).select_from(Deposit)
    if from_date is not None:
        query = query.where(Deposit.date >= from_date)
    if to_date is not None:
        query = query.where(Deposit.date <= to_date)
    if confirmed is not None:
        query = query.where(Deposit.confirmed == confirmed)
    result = await db.execute(query)
    return result.scalar_one()


async def get_deposit_payment_ids(db: AsyncSession, deposit_id: int) -> list[int]:
    result = await db.execute(
        select(deposit_payments.c.payment_id).where(deposit_payments.c.deposit_id == deposit_id)
    )
    return [row[0] for row in result.all()]


async def confirm_deposit(db: AsyncSession, deposit_id: int) -> Deposit:
    """Confirm a deposit (physically taken to the bank).

    At confirmation time:
    - Mark deposit as confirmed + set confirmed_date.
    - For especes: create CashEntry OUT (cash leaves the till for the bank).
    - For both types: generate accounting entries (caisse/chèques → banque).
    - For cheques: create a positive BankTransaction representing the credit.
    """
    deposit = await get_deposit(db, deposit_id)
    if deposit is None:
        raise LookupError("Deposit not found")
    if deposit.confirmed:
        raise ValueError("Deposit is already confirmed")

    deposit.confirmed = True
    deposit.confirmed_date = date.today()
    await db.flush()

    if deposit.type == DepositType.ESPECES:
        from backend.services.cash_service import create_cash_entry_record  # noqa: PLC0415

        reference = deposit.bank_reference or f"DEP-ESP-{deposit.id}"
        await create_cash_entry_record(
            db,
            date=deposit.confirmed_date,
            amount=deposit.total_amount,
            type=CashMovementType.OUT,
            reference=reference,
            description="Remise d'espèces en banque",
            source=CashEntrySource.DEPOSIT,
        )
        # Also credit the bank account so the bank balance is updated
        esp_tx = await create_bank_transaction_record(
            db,
            date=deposit.confirmed_date,
            amount=deposit.total_amount,
            reference=reference,
            description=f"Remise d'espèces (bordereau #{deposit.id})",
            source=BankTransactionSource.MANUAL,
        )
        esp_tx.detected_category = BankTransactionCategory.CASH_DEPOSIT
    else:
        # Cheques: create a bank transaction credit so the bank balance is updated
        reference = deposit.bank_reference or f"DEP-CHQ-{deposit.id}"
        chq_tx = await create_bank_transaction_record(
            db,
            date=deposit.confirmed_date,
            amount=deposit.total_amount,
            reference=reference,
            description=f"Remise de chèques (bordereau #{deposit.id})",
            source=BankTransactionSource.MANUAL,
        )
        chq_tx.detected_category = BankTransactionCategory.CHEQUE_DEPOSIT
        # Mark linked cheque payments as fully deposited
        result = await db.execute(
            select(Payment)
            .join(
                deposit_payments,
                Payment.id == deposit_payments.c.payment_id,
            )
            .where(deposit_payments.c.deposit_id == deposit.id)
        )
        for p in result.scalars().all():
            p.deposited = True
            p.in_deposit = False

    # Generate accounting entries (caisse/chèques → banque)
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_deposit,
    )

    await generate_entries_for_deposit(db, deposit)

    await db.flush()
    await db.refresh(deposit)
    return deposit
