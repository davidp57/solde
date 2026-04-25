"""Dashboard service — KPIs, alerts and monthly chart data."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import AccountingAccount, AccountType
from backend.models.accounting_entry import AccountingEntry
from backend.models.bank import BankTransaction
from backend.models.cash import CashRegister
from backend.models.fiscal_year import FiscalYear
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.models.payment import Payment, PaymentMethod


async def get_dashboard(db: AsyncSession) -> dict[str, object]:
    """Return dashboard KPIs and alerts."""
    today = date.today()

    # --- Bank balance (last transaction balance_after) ---
    bank_result = await db.execute(
        select(BankTransaction.balance_after)
        .order_by(BankTransaction.date.desc(), BankTransaction.id.desc())
        .limit(1)
    )
    bank_balance = bank_result.scalar_one_or_none() or Decimal("0")

    # --- Cash balance (last cash register entry balance_after) ---
    cash_result = await db.execute(
        select(CashRegister.balance_after)
        .order_by(CashRegister.date.desc(), CashRegister.id.desc())
        .limit(1)
    )
    cash_balance = cash_result.scalar_one_or_none() or Decimal("0")

    # --- Unpaid client invoices (total_amount > paid_amount, filtered in DB) ---
    unpaid_result = await db.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), Decimal("0")),
        ).where(
            Invoice.type == InvoiceType.CLIENT,
            Invoice.status != InvoiceStatus.DRAFT,
            Invoice.total_amount > Invoice.paid_amount,
        )
    )
    unpaid_row = unpaid_result.one()
    unpaid_count: int = unpaid_row[0] or 0
    unpaid_total: Decimal = unpaid_row[1] or Decimal("0")

    # --- Overdue invoices (remaining amount > 0 with due_date < today, filtered in DB) ---
    overdue_result = await db.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), Decimal("0")),
        ).where(
            Invoice.type == InvoiceType.CLIENT,
            Invoice.status != InvoiceStatus.DRAFT,
            Invoice.total_amount > Invoice.paid_amount,
            Invoice.due_date.is_not(None),
            Invoice.due_date < today,
        )
    )
    overdue_row = overdue_result.one()
    overdue_count: int = overdue_row[0] or 0
    overdue_total: Decimal = overdue_row[1] or Decimal("0")

    # --- Undeposited payments (client chèques/espèces not yet deposited) ---
    undeposited_result = await db.execute(
        select(func.count(Payment.id))
        .join(Invoice, Payment.invoice_id == Invoice.id)
        .where(
            Payment.deposited == False,  # noqa: E712
            Payment.method.in_([PaymentMethod.CHEQUE, PaymentMethod.ESPECES]),
            Invoice.type == InvoiceType.CLIENT,
        )
    )
    undeposited_count = undeposited_result.scalar_one_or_none() or 0

    # --- Current fiscal year result ---
    from backend.services.accounting_entry_service import (
        _compute_resultat,
    )  # noqa: PLC0415
    from backend.services.fiscal_year_service import get_current_fiscal_year  # noqa: PLC0415

    current_fy = await get_current_fiscal_year(db)
    current_fy_name: str | None = None
    current_resultat: Decimal = Decimal("0")

    if current_fy:
        current_fy_name = current_fy.name
        charges, produits = await _compute_resultat(db, current_fy.id)
        current_resultat = produits - charges

    # --- Alerts ---
    alerts: list[dict[str, str]] = []

    if overdue_count > 0:
        alerts.append(
            {
                "type": "warning",
                "message": f"{overdue_count} facture(s) en retard — {overdue_total:.2f} €",
            }
        )
    if undeposited_count > 0:
        alerts.append(
            {
                "type": "info",
                "message": f"{undeposited_count} paiement(s) non déposé(s) en banque.",
            }
        )

    return {
        "bank_balance": Decimal(str(bank_balance)),
        "cash_balance": Decimal(str(cash_balance)),
        "unpaid_count": unpaid_count,
        "unpaid_total": unpaid_total,
        "overdue_count": overdue_count,
        "overdue_total": overdue_total,
        "undeposited_count": undeposited_count,
        "current_fy_name": current_fy_name,
        "current_resultat": current_resultat,
        "alerts": alerts,
    }


def _month_start(value: date) -> date:
    return value.replace(day=1)


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


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _rolling_month_windows(months: int) -> list[tuple[str, date]]:
    today = date.today()
    current_month = _month_start(today)
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
        month_cursor = _next_month(month_cursor)
    return windows


async def _resolve_chart_fiscal_year(
    db: AsyncSession, fiscal_year_id: int | None
) -> FiscalYear | None:
    if fiscal_year_id is not None:
        result = await db.execute(select(FiscalYear).where(FiscalYear.id == fiscal_year_id))
        return result.scalar_one_or_none()

    from backend.services.fiscal_year_service import get_current_fiscal_year  # noqa: PLC0415

    return await get_current_fiscal_year(db)


async def get_monthly_chart(
    db: AsyncSession, fiscal_year_id: int | None
) -> list[dict[str, Decimal | str]]:
    """Return monthly income/expense data for a fiscal year."""
    fiscal_year = await _resolve_chart_fiscal_year(db, fiscal_year_id)
    if fiscal_year is None:
        return []

    # Get charge and produit accounts
    acct_result = await db.execute(
        select(AccountingAccount).where(
            AccountingAccount.type.in_([AccountType.CHARGE, AccountType.PRODUIT])
        )
    )
    acct_map = {a.number: a for a in acct_result.scalars().all()}

    # Get all entries for the fiscal year window
    entries_result = await db.execute(
        select(AccountingEntry).where(
            AccountingEntry.date >= fiscal_year.start_date,
            AccountingEntry.date <= fiscal_year.end_date,
        )
    )
    entries = entries_result.scalars().all()

    # Aggregate by month
    months: dict[str, dict[str, Decimal]] = {}
    current_month = _month_start(fiscal_year.start_date)
    final_month = _month_start(fiscal_year.end_date)
    while current_month <= final_month:
        month_key = current_month.strftime("%Y-%m")
        months[month_key] = {"charges": Decimal("0"), "produits": Decimal("0")}
        current_month = _next_month(current_month)

    for e in entries:
        acct = acct_map.get(e.account_number)
        if acct is None:
            continue
        month_key = e.date.strftime("%Y-%m")
        if month_key not in months:
            continue
        if acct.type == AccountType.CHARGE:
            months[month_key]["charges"] += e.debit - e.credit
        elif acct.type == AccountType.PRODUIT:
            months[month_key]["produits"] += e.credit - e.debit

    return [
        {
            "month": month_key,
            "charges": max(Decimal("0"), v["charges"]),
            "produits": max(Decimal("0"), v["produits"]),
        }
        for month_key, v in sorted(months.items())
    ]


async def get_resources_chart(
    db: AsyncSession,
    *,
    months: int = 12,
) -> list[dict[str, Decimal | str]]:
    from backend.services import bank_service, cash_service  # noqa: PLC0415

    windows = _rolling_month_windows(months)
    if not windows:
        return []

    max_period_end = windows[-1][1]
    bank_series = await bank_service.get_monthly_funds_series(db, months=months)
    cash_series = await cash_service.get_monthly_funds_series(db, months=months)
    bank_by_month = {row["month"]: Decimal(str(row["total"])) for row in bank_series}
    cash_by_month = {row["month"]: Decimal(str(row["balance"])) for row in cash_series}

    invoice_result = await db.execute(
        select(Invoice.id, Invoice.type, Invoice.date, Invoice.total_amount)
        .where(
            Invoice.status != InvoiceStatus.DRAFT,
            Invoice.date <= max_period_end,
        )
        .order_by(Invoice.date.asc(), Invoice.id.asc())
    )
    invoices = [
        (invoice_id, invoice_type, invoice_date, Decimal(str(total_amount)))
        for invoice_id, invoice_type, invoice_date, total_amount in invoice_result.all()
    ]

    payment_result = await db.execute(
        select(
            Payment.invoice_id,
            Invoice.type,
            Payment.date,
            Payment.amount,
            Payment.method,
            Payment.deposit_date,
        )
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .where(
            Invoice.status != InvoiceStatus.DRAFT,
            Invoice.date <= max_period_end,
            Payment.date <= max_period_end,
        )
        .order_by(Payment.date.asc(), Payment.id.asc())
    )
    payments = [
        (
            invoice_id,
            invoice_type,
            payment_date,
            Decimal(str(amount)),
            payment_method,
            deposit_date,
        )
        for (
            invoice_id,
            invoice_type,
            payment_date,
            amount,
            payment_method,
            deposit_date,
        ) in payment_result.all()
    ]
    cheque_deposit_events = sorted(
        (deposit_date, amount)
        for _, invoice_type, _, amount, payment_method, deposit_date in payments
        if invoice_type == InvoiceType.CLIENT
        and payment_method == PaymentMethod.CHEQUE
        and deposit_date is not None
    )

    rows: list[dict[str, Decimal | str]] = []
    active_remaining_by_invoice_id: dict[int, Decimal] = {}
    pending_paid_by_invoice_id: dict[int, Decimal] = {}
    client_receivables = Decimal("0")
    supplier_payables = Decimal("0")
    undeposited_cheques = Decimal("0")
    invoice_index = 0
    payment_index = 0
    cheque_deposit_index = 0
    for month_label, period_end in windows:
        while invoice_index < len(invoices) and invoices[invoice_index][2] <= period_end:
            invoice_id, invoice_type, _, total_amount = invoices[invoice_index]
            remaining_amount = total_amount - pending_paid_by_invoice_id.pop(
                invoice_id,
                Decimal("0"),
            )
            if remaining_amount < 0:
                remaining_amount = Decimal("0")
            active_remaining_by_invoice_id[invoice_id] = remaining_amount
            if invoice_type == InvoiceType.CLIENT:
                client_receivables += remaining_amount
            elif invoice_type == InvoiceType.FOURNISSEUR:
                supplier_payables += remaining_amount
            invoice_index += 1

        while payment_index < len(payments) and payments[payment_index][2] <= period_end:
            invoice_id, invoice_type, _, amount, payment_method, _ = payments[payment_index]
            active_remaining_amount = active_remaining_by_invoice_id.get(invoice_id)
            if active_remaining_amount is None:
                pending_paid_by_invoice_id[invoice_id] = (
                    pending_paid_by_invoice_id.get(
                        invoice_id,
                        Decimal("0"),
                    )
                    + amount
                )
            else:
                applied_amount = (
                    amount if amount <= active_remaining_amount else active_remaining_amount
                )
                active_remaining_by_invoice_id[invoice_id] = (
                    active_remaining_amount - applied_amount
                )
                if invoice_type == InvoiceType.CLIENT:
                    client_receivables -= applied_amount
                elif invoice_type == InvoiceType.FOURNISSEUR:
                    supplier_payables -= applied_amount
            if invoice_type == InvoiceType.CLIENT and payment_method == PaymentMethod.CHEQUE:
                undeposited_cheques += amount
            payment_index += 1

        while (
            cheque_deposit_index < len(cheque_deposit_events)
            and cheque_deposit_events[cheque_deposit_index][0] <= period_end
        ):
            undeposited_cheques -= cheque_deposit_events[cheque_deposit_index][1]
            cheque_deposit_index += 1

        liquidities = bank_by_month.get(month_label, Decimal("0")) + cash_by_month.get(
            month_label,
            Decimal("0"),
        )
        net_resources = liquidities + client_receivables + undeposited_cheques - supplier_payables
        rows.append(
            {
                "month": month_label,
                "funds": liquidities,
                "liquidities": liquidities,
                "client_receivables": client_receivables,
                "undeposited_cheques": undeposited_cheques,
                "supplier_payables": supplier_payables,
                "net_resources": net_resources,
            }
        )

    return rows
