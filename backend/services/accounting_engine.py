"""Accounting engine — applies configurable rules to generate journal entries.

This is the core of the accounting module. Rules are loaded from the DB and
applied whenever an accounting-triggering event occurs (invoice sent, payment
received, deposit created, etc.).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.accounting_entry import (
    AccountingEntry,
    EntrySourceType,
    build_entry_group_key,
)
from backend.models.accounting_rule import AccountingRule, AccountingRuleEntry, TriggerType
from backend.models.bank import Deposit, DepositType
from backend.models.invoice import Invoice, InvoiceLabel, InvoiceLine, InvoiceType
from backend.models.payment import Payment, PaymentMethod
from backend.services.fiscal_year_service import find_fiscal_year_id_for_date

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
    group_key: str | None = None,
) -> list[AccountingEntry]:
    """Create accounting entries for all rule_entries of a rule."""
    return await _apply_rule_entries(
        db,
        rule.entries,
        amount,
        entry_date,
        context,
        source_type,
        source_id,
        fiscal_year_id,
        group_key,
    )


async def _apply_rule_entries(
    db: AsyncSession,
    rule_entries: Sequence[AccountingRuleEntry],
    amount: Decimal,
    entry_date: date,
    context: Mapping[str, object],
    source_type: EntrySourceType | None,
    source_id: int | None,
    fiscal_year_id: int | None,
    group_key: str | None = None,
) -> list[AccountingEntry]:
    """Create accounting entries for a selected subset of rule entries."""
    created: list[AccountingEntry] = []
    resolved_group_key = group_key or build_entry_group_key(source_type, source_id)
    for rule_entry in rule_entries:
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
            group_key=resolved_group_key,
        )
        db.add(entry)
        await db.flush()  # ensure COUNT is accurate for the next entry in the loop
        created.append(entry)

    return created


def _normalize_invoice_line_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _classify_client_invoice_line(line: InvoiceLine) -> InvoiceLabel | None:
    if not (text := _normalize_invoice_line_text(line.description)):
        return None
    return (
        InvoiceLabel.ADHESION
        if "adhesion" in text
        else InvoiceLabel.CS
        if "cours" in text or "soutien" in text
        else None
    )


async def _generate_split_client_invoice_entries(
    db: AsyncSession,
    invoice: Invoice,
    *,
    context: Mapping[str, object],
    fiscal_year_id: int | None,
) -> list[AccountingEntry] | None:
    if (
        invoice.label != InvoiceLabel.CS_ADHESION
        or not invoice.has_explicit_breakdown
        or len(invoice.lines) < 2
    ):
        return None

    grouped_amounts: dict[InvoiceLabel, Decimal] = {}
    for line in invoice.lines:
        component_label = _classify_client_invoice_line(line)
        if component_label is None:
            return None
        grouped_amounts[component_label] = grouped_amounts.get(
            component_label,
            Decimal("0"),
        ) + Decimal(str(line.amount))

    if set(grouped_amounts) != {InvoiceLabel.CS, InvoiceLabel.ADHESION}:
        return None

    total_amount = sum(grouped_amounts.values(), Decimal("0"))
    if total_amount != Decimal(str(invoice.total_amount)):
        return None

    cs_a_rule = await _get_rule(db, TriggerType.INVOICE_CLIENT_CS_A)
    cs_rule = (
        await _get_rule(db, TriggerType.INVOICE_CLIENT_CS)
        if grouped_amounts[InvoiceLabel.CS] > 0
        else None
    )
    adhesion_rule = (
        await _get_rule(db, TriggerType.INVOICE_CLIENT_A)
        if grouped_amounts[InvoiceLabel.ADHESION] > 0
        else None
    )
    if cs_a_rule is None:
        return None
    if grouped_amounts[InvoiceLabel.CS] > 0 and cs_rule is None:
        return None
    if grouped_amounts[InvoiceLabel.ADHESION] > 0 and adhesion_rule is None:
        return None

    debit_entries = [entry for entry in cs_a_rule.entries if entry.side == "debit"]
    cs_credit_entries = [
        entry
        for entry in (cs_rule.entries if cs_rule is not None else [])
        if entry.side == "credit"
    ]
    adhesion_credit_entries = [
        entry
        for entry in (adhesion_rule.entries if adhesion_rule is not None else [])
        if entry.side == "credit"
    ]
    if not debit_entries:
        return None
    if grouped_amounts[InvoiceLabel.CS] > 0 and not cs_credit_entries:
        return None
    if grouped_amounts[InvoiceLabel.ADHESION] > 0 and not adhesion_credit_entries:
        return None

    created: list[AccountingEntry] = []
    created.extend(
        await _apply_rule_entries(
            db,
            debit_entries,
            total_amount,
            invoice.date,
            context,
            EntrySourceType.INVOICE,
            invoice.id,
            fiscal_year_id,
        )
    )
    if grouped_amounts[InvoiceLabel.CS] > 0:
        created.extend(
            await _apply_rule_entries(
                db,
                cs_credit_entries,
                grouped_amounts[InvoiceLabel.CS],
                invoice.date,
                context,
                EntrySourceType.INVOICE,
                invoice.id,
                fiscal_year_id,
            )
        )
    if grouped_amounts[InvoiceLabel.ADHESION] > 0:
        created.extend(
            await _apply_rule_entries(
                db,
                adhesion_credit_entries,
                grouped_amounts[InvoiceLabel.ADHESION],
                invoice.date,
                context,
                EntrySourceType.INVOICE,
                invoice.id,
                fiscal_year_id,
            )
        )
    return created


async def _apply_double_entry(
    db: AsyncSession,
    *,
    amount: Decimal,
    entry_date: date,
    label: str,
    debit_account: str,
    credit_account: str,
    source_type: EntrySourceType | None,
    source_id: int | None,
    fiscal_year_id: int | None,
    group_key: str | None = None,
) -> list[AccountingEntry]:
    """Create a basic debit/credit pair without relying on a persisted rule."""
    if amount <= 0:
        return []

    created: list[AccountingEntry] = []
    resolved_group_key = group_key or build_entry_group_key(source_type, source_id)
    for account_number, debit, credit in [
        (debit_account, amount, Decimal("0")),
        (credit_account, Decimal("0"), amount),
    ]:
        entry = AccountingEntry(
            entry_number=await _next_entry_number(db),
            date=entry_date,
            account_number=account_number,
            label=label,
            debit=debit,
            credit=credit,
            fiscal_year_id=fiscal_year_id,
            source_type=source_type,
            source_id=source_id,
            group_key=resolved_group_key,
        )
        db.add(entry)
        await db.flush()
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
    elif invoice.label == InvoiceLabel.CS:
        trigger = TriggerType.INVOICE_FOURNISSEUR_SUBCONTRACTING
    else:
        trigger = TriggerType.INVOICE_FOURNISSEUR_GENERAL

    rule = await _get_rule(db, trigger)
    if rule is None:
        return []

    fiscal_year_id = await find_fiscal_year_id_for_date(db, invoice.date)
    context = {
        "number": invoice.number,
        "contact": str(invoice.contact_id),
        "label": invoice.description or invoice.number,
        "amount": str(invoice.total_amount),
        "date": str(invoice.date),
    }

    split_entries = await _generate_split_client_invoice_entries(
        db,
        invoice,
        context=context,
        fiscal_year_id=fiscal_year_id,
    )
    if split_entries is not None:
        await db.flush()
        return split_entries

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
        method_map = {
            PaymentMethod.ESPECES: TriggerType.PAYMENT_SENT_ESPECES,
            PaymentMethod.CHEQUE: TriggerType.PAYMENT_SENT_VIREMENT,
            PaymentMethod.VIREMENT: TriggerType.PAYMENT_SENT_VIREMENT,
        }
        trigger = method_map.get(payment.method, TriggerType.PAYMENT_SENT_VIREMENT)

    rule = await _get_rule(db, trigger)
    if rule is None:
        return []

    fiscal_year_id = await find_fiscal_year_id_for_date(db, payment.date)
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

    fiscal_year_id = await find_fiscal_year_id_for_date(db, deposit.date)
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
    """Generate the accounting entries for a salary record:

    1. SALARY_GROSS   : 641000 D / 421000 C (gross amount)
    2. SALARY_EMPLOYEE_CHARGES : 421000 D / 431100 C (employee charges)
    3. SALARY_EMPLOYER_CHARGES : 645100 D / 431100 C (employer charges)
    4. SALARY_WITHHOLDING_TAX : 421000 D / 443000 C (withholding tax)
    5. SALARY_PAYMENT : 421000 D / 512100 C (net pay disbursed)

    Returns all generated entries (empty if no rules seeded).
    """

    # Derive a display date from the month (last day of month heuristic: use day 1 for simplicity)
    from datetime import date as _date  # noqa: PLC0415

    year_str, month_str = salary.month.split("-")
    entry_date = _date(int(year_str), int(month_str), 1)
    fiscal_year_id = await find_fiscal_year_id_for_date(db, entry_date)

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
    group_key = build_entry_group_key(EntrySourceType.SALARY, salary.id)

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
            group_key=group_key,
        )
        all_entries.extend(entries)

    legacy_salary_rules_present = any(
        rule is not None
        for rule in (
            rule_gross,
            await _get_rule(db, TriggerType.SALARY_EMPLOYER_CHARGES),
            await _get_rule(db, TriggerType.SALARY_PAYMENT),
        )
    )

    # 2. Employee charges
    employee_charges_amount = Decimal(str(salary.employee_charges))
    rule_employee_charges = await _get_rule(db, TriggerType.SALARY_EMPLOYEE_CHARGES)
    if rule_employee_charges and employee_charges_amount > 0:
        entries = await _apply_rule(
            db,
            rule_employee_charges,
            employee_charges_amount,
            entry_date,
            context,
            EntrySourceType.SALARY,
            salary.id,
            fiscal_year_id,
            group_key=group_key,
        )
        all_entries.extend(entries)
    elif legacy_salary_rules_present and employee_charges_amount > 0:
        entries = await _apply_double_entry(
            db,
            amount=employee_charges_amount,
            entry_date=entry_date,
            label=_render_template("Cotisations salariales {{employee}} {{month}}", context),
            debit_account="421000",
            credit_account="431100",
            source_type=EntrySourceType.SALARY,
            source_id=salary.id,
            fiscal_year_id=fiscal_year_id,
            group_key=group_key,
        )
        all_entries.extend(entries)

    # 3. Employer charges
    employer_charges_amount = Decimal(str(salary.employer_charges))
    rule_employer_charges = await _get_rule(db, TriggerType.SALARY_EMPLOYER_CHARGES)
    if rule_employer_charges and employer_charges_amount > 0:
        entries = await _apply_rule(
            db,
            rule_employer_charges,
            employer_charges_amount,
            entry_date,
            context,
            EntrySourceType.SALARY,
            salary.id,
            fiscal_year_id,
            group_key=group_key,
        )
        all_entries.extend(entries)

    # 4. Withholding tax
    withholding_tax_amount = Decimal(str(salary.tax))
    rule_withholding_tax = await _get_rule(db, TriggerType.SALARY_WITHHOLDING_TAX)
    if rule_withholding_tax and withholding_tax_amount > 0:
        entries = await _apply_rule(
            db,
            rule_withholding_tax,
            withholding_tax_amount,
            entry_date,
            context,
            EntrySourceType.SALARY,
            salary.id,
            fiscal_year_id,
            group_key=group_key,
        )
        all_entries.extend(entries)
    elif legacy_salary_rules_present and withholding_tax_amount > 0:
        entries = await _apply_double_entry(
            db,
            amount=withholding_tax_amount,
            entry_date=entry_date,
            label=_render_template("Impôt sur le revenu {{employee}} {{month}}", context),
            debit_account="421000",
            credit_account="443000",
            source_type=EntrySourceType.SALARY,
            source_id=salary.id,
            fiscal_year_id=fiscal_year_id,
            group_key=group_key,
        )
        all_entries.extend(entries)

    # 5. Net payment
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
            group_key=group_key,
        )
        all_entries.extend(entries)

    await db.flush()
    return all_entries


async def generate_entries_for_trigger(
    db: AsyncSession,
    trigger: TriggerType,
    amount: Decimal,
    entry_date: date,
    context: Mapping[str, object],
    *,
    source_type: EntrySourceType | None = None,
    source_id: int | None = None,
    group_key: str | None = None,
) -> list[AccountingEntry]:
    """Generate entries directly from a trigger when no dedicated domain object exists."""
    if amount <= 0:
        return []

    rule = await _get_rule(db, trigger)
    if rule is None:
        return []

    fiscal_year_id = await find_fiscal_year_id_for_date(db, entry_date)
    entries = await _apply_rule(
        db,
        rule,
        amount,
        entry_date,
        context,
        source_type,
        source_id,
        fiscal_year_id,
        group_key=group_key,
    )
    await db.flush()
    return entries


# ---------------------------------------------------------------------------
# Default rules seeding
# ---------------------------------------------------------------------------


async def seed_default_rules(db: AsyncSession) -> int:
    """Insert any missing default accounting rules.

    Returns the number of rules inserted (0 if already complete).
    """
    from backend.models.accounting_rule import (  # noqa: PLC0415
        DEFAULT_RULES,
        AccountingRuleEntry,
    )

    existing_rules = await db.execute(select(AccountingRule.trigger_type))
    existing_triggers: set[TriggerType] = {
        TriggerType(str(trigger_type)) for (trigger_type,) in existing_rules.all()
    }

    count = 0
    for rule_data in DEFAULT_RULES:
        trigger_type = cast(TriggerType, rule_data["trigger_type"])
        if trigger_type in existing_triggers:
            continue
        entries_data = cast(list[dict[str, object]], rule_data.pop("entries", []))
        rule = AccountingRule(**rule_data)
        db.add(rule)
        await db.flush()

        for entry_data in entries_data:
            rule_entry = AccountingRuleEntry(rule_id=rule.id, **entry_data)
            db.add(rule_entry)

        rule_data["entries"] = entries_data  # restore for idempotency
        count += 1
        existing_triggers.add(trigger_type)

    await db.commit()
    return count
