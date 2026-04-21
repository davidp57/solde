"""Bank service — transactions, deposit slips and reconciliation."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry
from backend.models.bank import (
    BankTransaction,
    BankTransactionCategory,
    BankTransactionSource,
    Deposit,
    DepositType,
    bank_transaction_payments,
    deposit_payments,
)
from backend.models.cash import CashEntrySource, CashMovementType
from backend.models.invoice import InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.schemas.bank import (
    BankTransactionClientPaymentsCreate,
    BankTransactionCreate,
    BankTransactionUpdate,
    DepositCreate,
)
from backend.services import payment as payment_service
from backend.services.bank_import import detect_transaction_category

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
    payment = await payment_service.get_payment(db, payment_id)
    if payment is None:
        raise LookupError("Payment not found")
    if payment.invoice_type != invoice_type or payment.method != PaymentMethod.VIREMENT:
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


def _build_reconciled_with_value(payments: list[Payment]) -> str | None:
    if not payments:
        return None
    if len(payments) == 1:
        return payments[0].invoice_number or payments[0].reference
    first_label = payments[0].invoice_number or payments[0].reference or f"payment-{payments[0].id}"
    return f"{first_label} +{len(payments) - 1}"


async def _store_transaction_payment_links(
    db: AsyncSession,
    *,
    tx: BankTransaction,
    payments: list[Payment],
) -> None:
    await db.execute(
        insert(bank_transaction_payments),
        [{"transaction_id": tx.id, "payment_id": payment.id} for payment in payments],
    )
    tx.reconciled = True
    tx.reconciled_with = _build_reconciled_with_value(payments)
    tx.payment_id = payments[0].id if len(payments) == 1 else None


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
    payments_total = sum((Decimal(str(payment.amount)) for payment in payments), start=Decimal("0"))
    if payments_total != expected_amount:
        raise ValueError(error_message)

    for payment in payments:
        payment.deposited = True
        payment.deposit_date = tx.date

    await _store_transaction_payment_links(db, tx=tx, payments=payments)
    await db.flush()
    await db.commit()
    await db.refresh(tx)
    return tx


async def _current_bank_balance(db: AsyncSession) -> Decimal:
    """Return the sum of all bank transaction amounts (positive = credit)."""
    result = await db.execute(select(func.sum(BankTransaction.amount)))
    total = result.scalar_one_or_none() or Decimal("0")
    return Decimal(str(total))


async def recompute_bank_balances(db: AsyncSession) -> bool:
    """Recompute running bank balances and report whether persisted values changed."""
    result = await db.execute(
        select(BankTransaction).order_by(BankTransaction.date.asc(), BankTransaction.id.asc())
    )
    running_balance = Decimal("0")
    changed = False
    for entry in result.scalars().all():
        running_balance += Decimal(str(entry.amount))
        if entry.balance_after != running_balance:
            entry.balance_after = running_balance
            changed = True
    return changed


async def add_transaction(db: AsyncSession, payload: BankTransactionCreate) -> BankTransaction:
    tx = await create_bank_transaction_record(
        db,
        date=payload.date,
        amount=payload.amount,
        reference=payload.reference,
        description=payload.description,
        source=payload.source,
    )
    await db.commit()
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
) -> BankTransaction:
    """Create a bank transaction without committing, then recompute balances."""
    tx = BankTransaction(
        date=date,
        amount=amount,
        reference=reference,
        description=description,
        balance_after=Decimal("0"),
        source=source,
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
    skip: int = 0,
    limit: int | None = None,
) -> list[BankTransaction]:
    query = select(BankTransaction)
    if from_date is not None:
        query = query.where(BankTransaction.date >= from_date)
    if to_date is not None:
        query = query.where(BankTransaction.date <= to_date)
    if unreconciled_only:
        query = query.where(BankTransaction.reconciled == False)  # noqa: E712
    query = query.order_by(BankTransaction.date.desc(), BankTransaction.id.desc())
    query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_monthly_funds_series(
    db: AsyncSession,
    *,
    months: int = 6,
) -> list[dict[str, Decimal | str]]:
    if await recompute_bank_balances(db):
        await db.commit()

    result = await db.execute(
        select(BankTransaction.date, BankTransaction.balance_after).order_by(
            BankTransaction.date.asc(), BankTransaction.id.asc()
        )
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
    await db.commit()
    await db.refresh(tx)
    return tx


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
        amount=Decimal(str(tx.amount)),
        payment_date=tx.date,
        reference=tx.reference,
        notes=tx.description or None,
    )

    await _store_transaction_payment_links(db, tx=tx, payments=[payment])
    await db.flush()
    await db.commit()
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

    expected_amount = Decimal(str(tx.amount))
    allocated_amount = sum(
        (Decimal(str(allocation.amount)) for allocation in payload.allocations),
        start=Decimal("0"),
    )
    if allocated_amount != expected_amount:
        raise ValueError("allocated amount must match bank transaction amount")

    payments: list[Payment] = []
    for allocation in payload.allocations:
        payment = await payment_service.create_bank_reconciled_client_payment(
            db,
            invoice_id=allocation.invoice_id,
            amount=Decimal(str(allocation.amount)),
            payment_date=tx.date,
            reference=tx.reference,
            notes=tx.description or None,
            commit=False,
        )
        payments.append(payment)

    await _store_transaction_payment_links(db, tx=tx, payments=payments)
    await db.flush()
    await db.commit()
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
        amount=abs(Decimal(str(tx.amount))),
        payment_date=tx.date,
        reference=tx.reference,
        notes=tx.description or None,
    )

    await _store_transaction_payment_links(db, tx=tx, payments=[payment])
    await db.flush()
    await db.commit()
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
        expected_amount=Decimal(str(tx.amount)),
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
        expected_amount=Decimal(str(tx.amount)),
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
        expected_amount=abs(Decimal(str(tx.amount))),
    )


async def get_bank_balance(db: AsyncSession) -> Decimal:
    return await _current_bank_balance(db)


# ---------------------------------------------------------------------------
# Deposit slips
# ---------------------------------------------------------------------------


async def create_deposit(db: AsyncSession, payload: DepositCreate) -> Deposit:
    """Create a deposit slip and mark its payments as deposited."""
    # Load payments and verify they exist
    result = await db.execute(select(Payment).where(Payment.id.in_(payload.payment_ids)))
    payments = list(result.scalars().all())
    if len(payments) != len(payload.payment_ids):
        raise ValueError("one or more payment_ids not found")

    expected_method = (
        PaymentMethod.CHEQUE if payload.type == DepositType.CHEQUES else PaymentMethod.ESPECES
    )
    invalid_payment = next(
        (payment for payment in payments if payment.method != expected_method),
        None,
    )
    if invalid_payment is not None:
        raise ValueError("deposit payments must match the selected deposit type")

    total_amount = sum((Decimal(str(payment.amount)) for payment in payments), Decimal("0"))

    deposit = Deposit(
        date=payload.date,
        type=payload.type,
        total_amount=total_amount,
        bank_reference=payload.bank_reference,
        notes=payload.notes,
    )
    db.add(deposit)
    await db.flush()

    # Create association rows
    await db.execute(
        insert(deposit_payments),
        [{"deposit_id": deposit.id, "payment_id": pid} for pid in payload.payment_ids],
    )

    # Mark payments as deposited
    for p in payments:
        p.deposited = True
        p.deposit_date = payload.date

    if payload.type == DepositType.ESPECES:
        from backend.services.cash_service import create_cash_entry_record  # noqa: PLC0415

        reference = payload.bank_reference or f"DEP-ESP-{deposit.id}"
        await create_cash_entry_record(
            db,
            date=payload.date,
            amount=total_amount,
            type=CashMovementType.OUT,
            reference=reference,
            description="Remise d'especes en banque",
            source=CashEntrySource.DEPOSIT,
        )

    # Auto-generate accounting entries
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_deposit,
    )

    await generate_entries_for_deposit(db, deposit)

    await db.commit()
    await db.refresh(deposit)
    return deposit


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
    skip: int = 0,
    limit: int | None = None,
) -> list[Deposit]:
    query = select(Deposit)
    if from_date is not None:
        query = query.where(Deposit.date >= from_date)
    if to_date is not None:
        query = query.where(Deposit.date <= to_date)
    query = query.order_by(Deposit.date.desc(), Deposit.id.desc()).offset(skip)
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_deposit_payment_ids(db: AsyncSession, deposit_id: int) -> list[int]:
    result = await db.execute(
        select(deposit_payments.c.payment_id).where(deposit_payments.c.deposit_id == deposit_id)
    )
    return [row[0] for row in result.all()]
