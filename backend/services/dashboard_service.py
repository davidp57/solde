"""Dashboard service — KPIs, alerts and monthly chart data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_entry import AccountingEntry
from backend.models.bank import BankTransaction
from backend.models.cash import CashRegister
from backend.models.invoice import Invoice, InvoiceStatus
from backend.models.payment import Payment


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

    # --- Unpaid invoices (status != paid, type=client) ---
    unpaid_result = await db.execute(
        select(Invoice).where(
            Invoice.type == "client",
            Invoice.status.in_(
                [
                    InvoiceStatus.SENT,
                    InvoiceStatus.PARTIAL,
                    InvoiceStatus.OVERDUE,
                    InvoiceStatus.DISPUTED,
                ]
            ),
        )
    )
    unpaid_invoices = unpaid_result.scalars().all()
    unpaid_count = len(unpaid_invoices)
    unpaid_total = sum(
        Decimal(str(inv.total_amount)) - Decimal(str(inv.paid_amount)) for inv in unpaid_invoices
    )

    # --- Overdue invoices (sent/partial/overdue with due_date < today) ---
    overdue_result = await db.execute(
        select(Invoice).where(
            Invoice.type == "client",
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]),
            Invoice.due_date < today,
        )
    )
    overdue_invoices = overdue_result.scalars().all()
    overdue_count = len(overdue_invoices)
    overdue_total = sum(
        Decimal(str(inv.total_amount)) - Decimal(str(inv.paid_amount)) for inv in overdue_invoices
    )

    # --- Undeposited payments (chèques/espèces not yet deposited) ---
    undeposited_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.deposited == False)  # noqa: E712
    )
    undeposited_count = undeposited_result.scalar_one_or_none() or 0

    # --- Current fiscal year result ---
    from backend.models.fiscal_year import FiscalYear, FiscalYearStatus  # noqa: PLC0415
    from backend.services.accounting_entry_service import (
        _compute_resultat,
    )  # noqa: PLC0415

    fy_result = await db.execute(
        select(FiscalYear)
        .where(FiscalYear.status == FiscalYearStatus.OPEN)
        .order_by(FiscalYear.start_date.asc())
        .limit(1)
    )
    current_fy = fy_result.scalar_one_or_none()
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


async def get_monthly_chart(db: AsyncSession, year: int) -> list[dict[str, Decimal | str]]:
    """Return monthly income/expense data for a given year (for charts)."""
    from backend.models.accounting_account import (
        AccountingAccount,
        AccountType,
    )  # noqa: PLC0415

    # Get charge and produit accounts
    acct_result = await db.execute(
        select(AccountingAccount).where(
            AccountingAccount.type.in_([AccountType.CHARGE, AccountType.PRODUIT])
        )
    )
    acct_map = {a.number: a for a in acct_result.scalars().all()}

    # Get all entries for the year
    entries_result = await db.execute(
        select(AccountingEntry).where(func.strftime("%Y", AccountingEntry.date) == str(year))
    )
    entries = entries_result.scalars().all()

    # Aggregate by month
    months: dict[str, dict[str, Decimal]] = {}
    for month_n in range(1, 13):
        month_key = f"{year}-{month_n:02d}"
        months[month_key] = {"charges": Decimal("0"), "produits": Decimal("0")}

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
