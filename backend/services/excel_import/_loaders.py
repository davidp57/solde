"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import._salary import (
    _salary_employee_key,
    _salary_month_group_signatures,
    _salary_month_standalone_tax_signatures,
)
from backend.services.excel_import_parsing import (
    format_contact_display_name as _format_contact_display_name,
)
from backend.services.excel_import_parsing import (
    normalize_text as _normalize_text,
)
from backend.services.excel_import_types import (
    NormalizedBankRow,
    NormalizedPaymentRow,
    NormalizedSalaryRow,
)


def _direct_bank_trigger_from_row(bank_row: NormalizedBankRow) -> tuple[Any, Decimal] | None:
    from backend.models.accounting_rule import TriggerType  # noqa: PLC0415

    description = _normalize_text(bank_row.description)
    reference = _normalize_text(bank_row.reference)
    combined_text = " ".join(part for part in (description, reference) if part)
    if "remise cheq" in combined_text and bank_row.amount > 0:
        return TriggerType.DEPOSIT_CHEQUES, bank_row.amount
    if "remise espe" in combined_text and bank_row.amount > 0:
        return TriggerType.DEPOSIT_ESPECES, bank_row.amount
    if "frais banc" in combined_text and bank_row.amount < 0:
        return TriggerType.BANK_FEES, abs(bank_row.amount)
    if "maif" in combined_text and bank_row.amount < 0:
        return TriggerType.BANK_INSURANCE, abs(bank_row.amount)
    if "interets" in combined_text and "livret bleu" in combined_text and bank_row.amount > 0:
        return TriggerType.BANK_SAVINGS_INTEREST, bank_row.amount
    if "virement interne" in combined_text:
        if bank_row.amount > 0:
            return TriggerType.BANK_INTERNAL_TRANSFER_FROM_SAVINGS, bank_row.amount
        if bank_row.amount < 0:
            return TriggerType.BANK_INTERNAL_TRANSFER_TO_SAVINGS, abs(bank_row.amount)
    if "urssaf" in combined_text and bank_row.amount < 0:
        return TriggerType.BANK_SOCIAL_CHARGES, abs(bank_row.amount)
    if "subvention" in combined_text and bank_row.amount > 0:
        return TriggerType.SUBSIDY_RECEIVED, bank_row.amount
    return None


async def _generate_direct_bank_entries(
    db: AsyncSession,
    *,
    bank_row: NormalizedBankRow,
    bank_entry: Any,
) -> list[Any]:
    from backend.models.accounting_entry import EntrySourceType  # noqa: PLC0415
    from backend.services.accounting_engine import generate_entries_for_trigger  # noqa: PLC0415

    direct_trigger = _direct_bank_trigger_from_row(bank_row)
    if direct_trigger is None:
        return []

    trigger, amount = direct_trigger
    return await generate_entries_for_trigger(
        db,
        trigger,
        amount,
        bank_row.entry_date,
        {
            "label": bank_row.description,
            "date": str(bank_row.entry_date),
        },
        source_type=EntrySourceType.GESTION,
        source_id=bank_entry.id,
    )


def _payment_signature(
    *,
    invoice_id: int,
    payment_date: date,
    amount: Decimal,
    method: str,
    cheque_number: str | None = None,
) -> tuple[int, str, str, str, str]:
    return (
        invoice_id,
        payment_date.isoformat(),
        format(amount.normalize(), "f"),
        _normalize_text(method),
        _normalize_text(cheque_number or "") if _normalize_text(method) == "cheque" else "",
    )


def _payment_row_from_bank_row(
    row: NormalizedBankRow,
    *,
    invoice_reference: str,
) -> NormalizedPaymentRow:
    return NormalizedPaymentRow(
        source_row_number=row.source_row_number,
        payment_date=row.entry_date,
        amount=row.amount,
        method="virement",
        invoice_ref=invoice_reference,
        contact_name="",
        cheque_number=None,
        deposited=True,
        deposit_date=row.entry_date,
    )


async def _load_existing_payment_signatures(
    db: AsyncSession,
) -> set[tuple[int, str, str, str, str]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.payment import Payment  # noqa: PLC0415

    result = await db.execute(
        select(
            Payment.invoice_id,
            Payment.date,
            Payment.amount,
            Payment.method,
            Payment.cheque_number,
        )
    )
    return {
        _payment_signature(
            invoice_id=invoice_id,
            payment_date=payment_date,
            amount=amount,
            method=str(method),
            cheque_number=cheque_number,
        )
        for invoice_id, payment_date, amount, method, cheque_number in result.all()
    }


async def _load_existing_contacts_by_salary_key(db: AsyncSession) -> dict[str, Any]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415

    result = await db.execute(select(Contact))
    contacts_by_key: dict[str, Any] = {}
    for contact in result.scalars().all():
        display_name = _format_contact_display_name(contact.nom, contact.prenom) or contact.nom
        contacts_by_key.setdefault(_salary_employee_key(display_name), contact)
        contacts_by_key.setdefault(_salary_employee_key(contact.nom), contact)
    return contacts_by_key


async def _load_existing_salary_keys(db: AsyncSession) -> set[tuple[str, str]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415

    result = await db.execute(select(Salary.month, Contact.nom, Contact.prenom).join(Contact))
    return {
        (month, _salary_employee_key(_format_contact_display_name(nom, prenom) or nom))
        for month, nom, prenom in result.all()
    }


async def _load_existing_salary_group_signatures(
    db: AsyncSession,
) -> dict[str, set[tuple[str, ...]]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415

    result = await db.execute(
        select(
            Salary.month,
            Contact.nom,
            Contact.prenom,
            Salary.hours,
            Salary.gross,
            Salary.employee_charges,
            Salary.employer_charges,
            Salary.tax,
            Salary.net_pay,
        ).join(Contact)
    )

    salaries_by_month: dict[str, list[NormalizedSalaryRow]] = {}
    for (
        month,
        nom,
        prenom,
        hours,
        gross,
        employee_charges,
        employer_charges,
        tax,
        net_pay,
    ) in result.all():
        salaries_by_month.setdefault(month, []).append(
            NormalizedSalaryRow(
                source_row_number=0,
                month=month,
                employee_name=_format_contact_display_name(nom, prenom) or nom,
                hours=Decimal(str(hours)),
                gross=Decimal(str(gross)),
                employee_charges=Decimal(str(employee_charges)),
                employer_charges=Decimal(str(employer_charges)),
                tax=Decimal(str(tax)),
                net_pay=Decimal(str(net_pay)),
            )
        )

    return {
        month: _salary_month_group_signatures(month, salary_rows)
        | _salary_month_standalone_tax_signatures(month, salary_rows)
        for month, salary_rows in salaries_by_month.items()
    }
