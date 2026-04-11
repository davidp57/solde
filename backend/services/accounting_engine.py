"""Accounting engine — applies configurable rules to generate journal entries.

This is the core of the accounting module. Rules are loaded from the DB and
applied whenever an accounting-triggering event occurs (invoice sent, payment
received, deposit created, etc.).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.accounting_rule import AccountingRule, TriggerType
from backend.models.bank import Deposit, DepositType
from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.models.invoice import Invoice, InvoiceLabel, InvoiceType
from backend.models.payment import Payment, PaymentMethod

if TYPE_CHECKING:
    from backend.models.salary import Salary

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _next_entry_number(db: AsyncSession) -> str:
    """Return the next sequential entry number (globally unique, 6 digits)."""
    result = await db.execute(select(func.count(AccountingEntry.id)))
    count = result.scalar_one_or_none() or 0
    return f"{count + 1:06d}"


async def _current_fiscal_year_id(db: AsyncSession) -> int | None:
    """Return the ID of the currently open fiscal year, or None."""
    result = await db.execute(
        select(FiscalYear.id).where(FiscalYear.status == FiscalYearStatus.OPEN).limit(1)
    )
    return result.scalar_one_or_none()


def _render_template(template: str, context: Mapping[str, object]) -> str:
    """Replace {{key}} placeholders in a template string with context values."""

    def replace(m: re.Match[str]) -> str:
        key = m.group(1).strip()
        return str(context.get(key, m.group(0)))

    return re.sub(r"\{\{(\w+)\}\}", replace, template)


async def _apply_rule(
    db: AsyncSession,
    rule: AccountingRule,
    amount: Decimal,
    entry_date: date,
    context: Mapping[str, object],
    source_type: EntrySourceType | None,
    source_id: int | None,
    fiscal_year_id: int | None,
) -> list[AccountingEntry]:
    """Create accounting entries for all rule_entries of a rule."""
    created: list[AccountingEntry] = []
    for rule_entry in rule.entries:
        entry_number = await _next_entry_number(db)
        label = _render_template(rule_entry.description_template, context)

        debit = amount if rule_entry.side == "debit" else Decimal("0")
        credit = amount if rule_entry.side == "credit" else Decimal("0")

        entry = AccountingEntry(
            entry_number=entry_number,
            date=entry_date,
            account_number=rule_entry.account_number,
            label=label,
            debit=debit,
            credit=credit,
            fiscal_year_id=fiscal_year_id,
            source_type=source_type,
            source_id=source_id,
        )
        db.add(entry)
        await db.flush()  # ensure COUNT is accurate for the next entry in the loop
        created.append(entry)

    return created


async def _get_rule(db: AsyncSession, trigger: TriggerType) -> AccountingRule | None:
    """Load an active rule with its entries for the given trigger type."""
    result = await db.execute(
        select(AccountingRule)
        .where(AccountingRule.trigger_type == trigger)
        .where(AccountingRule.is_active == True)  # noqa: E712
        .options(selectinload(AccountingRule.entries))
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Public entry points — called by invoice/payment/bank services
# ---------------------------------------------------------------------------


async def generate_entries_for_invoice(
    db: AsyncSession,
    invoice: Invoice,
) -> list[AccountingEntry]:
    """Generate accounting entries when an invoice is sent/confirmed.

    Determines trigger type from invoice.type + invoice.label.
    Returns an empty list if no matching active rule exists.
    """
    if invoice.type == InvoiceType.CLIENT:
        label_map: dict[InvoiceLabel | None, TriggerType] = {
            InvoiceLabel.CS: TriggerType.INVOICE_CLIENT_CS,
            InvoiceLabel.ADHESION: TriggerType.INVOICE_CLIENT_A,
            InvoiceLabel.CS_ADHESION: TriggerType.INVOICE_CLIENT_CS_A,
            InvoiceLabel.GENERAL: TriggerType.INVOICE_CLIENT_GENERAL,
            None: TriggerType.INVOICE_CLIENT_GENERAL,
        }
        trigger = label_map.get(invoice.label, TriggerType.INVOICE_CLIENT_GENERAL)
    else:
        # Fournisseur — use CS as proxy for sous-traitance (label-based heuristic)
        if invoice.label == InvoiceLabel.CS:
            trigger = TriggerType.INVOICE_FOURNISSEUR_SUBCONTRACTING
        else:
            trigger = TriggerType.INVOICE_FOURNISSEUR_GENERAL

    rule = await _get_rule(db, trigger)
    if rule is None:
        return []

    fiscal_year_id = await _current_fiscal_year_id(db)
    context = {
        "number": invoice.number,
        "contact": str(invoice.contact_id),
        "label": invoice.description or invoice.number,
        "amount": str(invoice.total_amount),
        "date": str(invoice.date),
    }

    entries = await _apply_rule(
        db,
        rule,
        Decimal(str(invoice.total_amount)),
        invoice.date,
        context,
        EntrySourceType.INVOICE,
        invoice.id,
        fiscal_year_id,
    )
    await db.flush()
    return entries


async def generate_entries_for_payment(
    db: AsyncSession,
    payment: Payment,
    invoice_type: InvoiceType,
) -> list[AccountingEntry]:
    """Generate accounting entries for a received or sent payment.

    Returns an empty list if no matching active rule exists.
    """
    if invoice_type == InvoiceType.CLIENT:
        method_map = {
            PaymentMethod.ESPECES: TriggerType.PAYMENT_RECEIVED_ESPECES,
            PaymentMethod.CHEQUE: TriggerType.PAYMENT_RECEIVED_CHEQUE,
            PaymentMethod.VIREMENT: TriggerType.PAYMENT_RECEIVED_VIREMENT,
        }
        trigger = method_map.get(payment.method, TriggerType.PAYMENT_RECEIVED_VIREMENT)
    else:
        # Fournisseur payments are always virements
        trigger = TriggerType.PAYMENT_SENT_VIREMENT

    rule = await _get_rule(db, trigger)
    if rule is None:
        return []

    fiscal_year_id = await _current_fiscal_year_id(db)
    context = {
        "label": f"Règlement facture #{payment.invoice_id}",
        "amount": str(payment.amount),
        "date": str(payment.date),
        "method": str(payment.method),
    }
    if payment.cheque_number:
        context["label"] = f"Chèque {payment.cheque_number}"

    entries = await _apply_rule(
        db,
        rule,
        Decimal(str(payment.amount)),
        payment.date,
        context,
        EntrySourceType.PAYMENT,
        payment.id,
        fiscal_year_id,
    )
    await db.flush()
    return entries


async def generate_entries_for_deposit(
    db: AsyncSession,
    deposit: Deposit,
) -> list[AccountingEntry]:
    """Generate accounting entries when a deposit slip is finalised.

    Returns an empty list if no matching active rule exists.
    """
    trigger_map = {
        DepositType.ESPECES: TriggerType.DEPOSIT_ESPECES,
        DepositType.CHEQUES: TriggerType.DEPOSIT_CHEQUES,
    }
    trigger = trigger_map.get(deposit.type, TriggerType.DEPOSIT_ESPECES)

    rule = await _get_rule(db, trigger)
    if rule is None:
        return []

    fiscal_year_id = await _current_fiscal_year_id(db)
    context = {
        "label": f"Bordereau #{deposit.id} — {deposit.type}",
        "amount": str(deposit.total_amount),
        "date": str(deposit.date),
    }

    entries = await _apply_rule(
        db,
        rule,
        Decimal(str(deposit.total_amount)),
        deposit.date,
        context,
        EntrySourceType.DEPOSIT,
        deposit.id,
        fiscal_year_id,
    )
    await db.flush()
    return entries


async def generate_entries_for_salary(
    db: AsyncSession,
    salary: Salary,
) -> list[AccountingEntry]:
    """Generate three sets of entries for a salary record:

    1. SALARY_GROSS   : 641000 D / 421000 C (gross amount)
    2. SALARY_EMPLOYER_CHARGES : 645100 D / 431100 C (employer charges)
    3. SALARY_PAYMENT : 421000 D / 512100 C (net pay disbursed)

    Returns all generated entries (empty if no rules seeded).
    """

    fiscal_year_id = await _current_fiscal_year_id(db)

    # Derive a display date from the month (last day of month heuristic: use day 1 for simplicity)
    from datetime import date as _date  # noqa: PLC0415

    year_str, month_str = salary.month.split("-")
    entry_date = _date(int(year_str), int(month_str), 1)

    employee_name = ""
    if salary.employee:
        parts = []
        if salary.employee.prenom:
            parts.append(salary.employee.prenom)
        if salary.employee.nom:
            parts.append(salary.employee.nom)
        employee_name = " ".join(parts)

    context = {
        "employee": employee_name,
        "month": salary.month,
        "date": str(entry_date),
    }

    all_entries: list[AccountingEntry] = []

    # 1. Gross salary
    rule_gross = await _get_rule(db, TriggerType.SALARY_GROSS)
    if rule_gross and Decimal(str(salary.gross)) > 0:
        entries = await _apply_rule(
            db,
            rule_gross,
            Decimal(str(salary.gross)),
            entry_date,
            context,
            EntrySourceType.SALARY,
            salary.id,
            fiscal_year_id,
        )
        all_entries.extend(entries)

    # 2. Employer charges
    rule_charges = await _get_rule(db, TriggerType.SALARY_EMPLOYER_CHARGES)
    if rule_charges and Decimal(str(salary.employer_charges)) > 0:
        entries = await _apply_rule(
            db,
            rule_charges,
            Decimal(str(salary.employer_charges)),
            entry_date,
            context,
            EntrySourceType.SALARY,
            salary.id,
            fiscal_year_id,
        )
        all_entries.extend(entries)

    # 3. Net payment
    rule_payment = await _get_rule(db, TriggerType.SALARY_PAYMENT)
    if rule_payment and Decimal(str(salary.net_pay)) > 0:
        entries = await _apply_rule(
            db,
            rule_payment,
            Decimal(str(salary.net_pay)),
            entry_date,
            context,
            EntrySourceType.SALARY,
            salary.id,
            fiscal_year_id,
        )
        all_entries.extend(entries)

    await db.flush()
    return all_entries


# ---------------------------------------------------------------------------
# Default rules seeding
# ---------------------------------------------------------------------------


async def seed_default_rules(db: AsyncSession) -> int:
    """Insert default accounting rules if the table is empty.

    Returns the number of rules inserted (0 if already seeded).
    """
    from backend.models.accounting_rule import (  # noqa: PLC0415
        DEFAULT_RULES,
        AccountingRuleEntry,
    )

    existing = await db.execute(select(func.count(AccountingRule.id)))
    if (existing.scalar_one_or_none() or 0) > 0:
        return 0

    count = 0
    for rule_data in DEFAULT_RULES:
        entries_data = cast(list[dict[str, object]], rule_data.pop("entries", []))
        rule = AccountingRule(**rule_data)
        db.add(rule)
        await db.flush()

        for entry_data in entries_data:
            rule_entry = AccountingRuleEntry(rule_id=rule.id, **entry_data)
            db.add(rule_entry)

        rule_data["entries"] = entries_data  # restore for idempotency
        count += 1

    await db.commit()
    return count
