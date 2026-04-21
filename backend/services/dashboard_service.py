"""Dashboard service — KPIs, alerts and monthly chart data."""

from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
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

    def remaining_amount(invoice: Invoice) -> Decimal:
        return Decimal(str(invoice.total_amount)) - Decimal(str(invoice.paid_amount))

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

    # --- Client invoices with a remaining amount (status can be stale after imports/edits) ---
    client_invoices_result = await db.execute(
        select(Invoice).where(
            Invoice.type == "client",
            Invoice.status != InvoiceStatus.DRAFT,
        )
    )
    client_invoices = client_invoices_result.scalars().all()
    unpaid_invoices = [invoice for invoice in client_invoices if remaining_amount(invoice) > 0]
    unpaid_count = len(unpaid_invoices)
    unpaid_total = sum(remaining_amount(inv) for inv in unpaid_invoices)

    # --- Overdue invoices (remaining amount > 0 with due_date < today) ---
    overdue_invoices = [
        invoice
        for invoice in unpaid_invoices
        if invoice.due_date is not None and invoice.due_date < today
    ]
    overdue_count = len(overdue_invoices)
    overdue_total = sum(remaining_amount(inv) for inv in overdue_invoices)

    # --- Undeposited payments (chèques/espèces not yet deposited) ---
    undeposited_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.deposited == False)  # noqa: E712
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
            months[month_key]["charges"] += Decimal(str(e.debit)) - Decimal(str(e.credit))
        elif acct.type == AccountType.PRODUIT:
            months[month_key]["produits"] += Decimal(str(e.credit)) - Decimal(str(e.debit))

    return [
        {
            "month": month_key,
            "charges": max(Decimal("0"), v["charges"]),
            "produits": max(Decimal("0"), v["produits"]),
        }
        for month_key, v in sorted(months.items())
    ]


def _remaining_amount_as_of(
    invoice: Invoice,
    *,
    payment_totals_by_invoice_id: dict[int, list[tuple[date, Decimal]]],
    period_end: date,
) -> Decimal:
    paid_amount = sum(
        (
            amount
            for payment_date, amount in payment_totals_by_invoice_id.get(invoice.id, [])
            if payment_date <= period_end
        ),
        Decimal("0"),
    )
    remaining_amount = Decimal(str(invoice.total_amount)) - paid_amount
    return remaining_amount if remaining_amount > 0 else Decimal("0")


async def get_resources_chart(
    db: AsyncSession,
    *,
    months: int = 12,
) -> list[dict[str, Decimal | str]]:
    from backend.services import bank_service, cash_service  # noqa: PLC0415

    windows = _rolling_month_windows(months)
    bank_series = await bank_service.get_monthly_funds_series(db, months=months)
    cash_series = await cash_service.get_monthly_funds_series(db, months=months)
    bank_by_month = {row["month"]: Decimal(str(row["total"])) for row in bank_series}
    cash_by_month = {row["month"]: Decimal(str(row["balance"])) for row in cash_series}

    invoice_result = await db.execute(select(Invoice).where(Invoice.status != InvoiceStatus.DRAFT))
    invoices = invoice_result.scalars().all()

    payment_result = await db.execute(
        select(Payment, Invoice.type).join(Invoice, Invoice.id == Payment.invoice_id)
    )
    payment_rows = payment_result.all()

    payment_totals_by_invoice_id: dict[int, list[tuple[date, Decimal]]] = defaultdict(list)
    cheque_rows: list[tuple[date, Decimal, date | None]] = []
    for payment, invoice_type in payment_rows:
        payment_totals_by_invoice_id[payment.invoice_id].append(
            (payment.date, Decimal(str(payment.amount)))
        )
        if invoice_type == InvoiceType.CLIENT and payment.method == PaymentMethod.CHEQUE:
            cheque_rows.append(
                (
                    payment.date,
                    Decimal(str(payment.amount)),
                    payment.deposit_date,
                )
            )

    rows: list[dict[str, Decimal | str]] = []
    for month_label, period_end in windows:
        client_receivables = sum(
            (
                _remaining_amount_as_of(
                    invoice,
                    payment_totals_by_invoice_id=payment_totals_by_invoice_id,
                    period_end=period_end,
                )
                for invoice in invoices
                if invoice.type == InvoiceType.CLIENT and invoice.date <= period_end
            ),
            Decimal("0"),
        )
        supplier_payables = sum(
            (
                _remaining_amount_as_of(
                    invoice,
                    payment_totals_by_invoice_id=payment_totals_by_invoice_id,
                    period_end=period_end,
                )
                for invoice in invoices
                if invoice.type == InvoiceType.FOURNISSEUR and invoice.date <= period_end
            ),
            Decimal("0"),
        )
        undeposited_cheques = sum(
            (
                amount
                for payment_date, amount, deposit_date in cheque_rows
                if payment_date <= period_end
                and (deposit_date is None or deposit_date > period_end)
            ),
            Decimal("0"),
        )
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
