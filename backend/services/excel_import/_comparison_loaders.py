"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import._comparison import (
    _gestion_bank_comparison_signature,
    _gestion_cash_comparison_signature,
    _gestion_payment_comparison_signature,
    _gestion_salary_comparison_signature,
    _is_within_date_bounds,
    _make_gestion_bank_extra_detail,
    _make_gestion_cash_extra_detail,
    _make_gestion_invoice_extra_detail,
    _make_gestion_payment_extra_detail,
    _make_gestion_salary_extra_detail,
)
from backend.services.excel_import._invoices import _client_settlement_account_from_method
from backend.services.excel_import_parsing import (
    format_contact_display_name as _format_contact_display_name,
)
from backend.services.excel_import_parsing import (
    normalize_text as _normalize_text,
)


async def _load_existing_client_invoice_comparison_signatures(
    db: AsyncSession,
    years: set[int],
    start_date: date | None = None,
    end_date: date | None = None,
) -> set[str]:
    if not years:
        return set()

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415

    result = await db.execute(
        select(Invoice.number, Invoice.date).where(Invoice.type == InvoiceType.CLIENT)
    )
    return {
        _normalize_text(number)
        for number, invoice_date in result.all()
        if number
        and invoice_date.year in years
        and _is_within_date_bounds(invoice_date, start_date, end_date)
    }


async def _load_existing_client_payment_comparison_signatures(
    db: AsyncSession,
    years: set[int],
    start_date: date | None = None,
    end_date: date | None = None,
) -> set[tuple[str, str, str, str, str]]:
    if not years:
        return set()

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    result = await db.execute(
        select(
            Invoice.number,
            Invoice.reference,
            Payment.date,
            Payment.amount,
            Payment.method,
            Payment.cheque_number,
        )
        .join(Payment, Payment.invoice_id == Invoice.id)
        .where(Invoice.type == InvoiceType.CLIENT)
    )

    signatures: set[tuple[str, str, str, str, str]] = set()
    for number, reference, payment_date, amount, method, cheque_number in result.all():
        if payment_date.year not in years or not _is_within_date_bounds(
            payment_date,
            start_date,
            end_date,
        ):
            continue
        references = {number}
        if reference:
            references.add(reference)
        settlement_account = _client_settlement_account_from_method(str(method))
        for candidate_reference in references:
            if not candidate_reference:
                continue
            signatures.add(
                _gestion_payment_comparison_signature(
                    reference=candidate_reference,
                    payment_date=payment_date,
                    amount=amount,
                    settlement_account=settlement_account,
                    cheque_number=cheque_number,
                )
            )
    return signatures


async def _load_existing_client_invoice_comparison_items(
    db: AsyncSession,
    years: set[int],
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, dict[str, str]]:
    if not years:
        return {}

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415

    result = await db.execute(
        select(Invoice.number, Invoice.date).where(Invoice.type == InvoiceType.CLIENT)
    )
    details: dict[str, dict[str, str]] = {}
    for number, invoice_date in result.all():
        if (
            not number
            or invoice_date.year not in years
            or not _is_within_date_bounds(invoice_date, start_date, end_date)
        ):
            continue
        details[_normalize_text(number)] = _make_gestion_invoice_extra_detail(number, invoice_date)
    return details


async def _load_existing_client_payment_comparison_items(
    db: AsyncSession,
    years: set[int],
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[tuple[str, str, str, str, str], dict[str, str]]:
    if not years:
        return {}

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    result = await db.execute(
        select(
            Invoice.number,
            Invoice.reference,
            Payment.date,
            Payment.amount,
            Payment.method,
            Payment.cheque_number,
        )
        .join(Payment, Payment.invoice_id == Invoice.id)
        .where(Invoice.type == InvoiceType.CLIENT)
    )

    details: dict[tuple[str, str, str, str, str], dict[str, str]] = {}
    for number, reference, payment_date, amount, method, cheque_number in result.all():
        if payment_date.year not in years or not _is_within_date_bounds(
            payment_date,
            start_date,
            end_date,
        ):
            continue
        candidate_references = [candidate for candidate in (number, reference) if candidate]
        seen_references: set[str] = set()
        settlement_account = _client_settlement_account_from_method(str(method))
        for candidate_reference in candidate_references:
            normalized_reference = _normalize_text(candidate_reference)
            if not normalized_reference or normalized_reference in seen_references:
                continue
            seen_references.add(normalized_reference)
            signature = _gestion_payment_comparison_signature(
                reference=candidate_reference,
                payment_date=payment_date,
                amount=amount,
                settlement_account=settlement_account,
                cheque_number=cheque_number,
            )
            details[signature] = _make_gestion_payment_extra_detail(
                reference=candidate_reference,
                payment_date=payment_date,
                amount=amount,
                settlement_account=settlement_account,
                cheque_number=cheque_number,
                invoice_number=number,
                invoice_reference=reference,
            )
    return details


async def _load_existing_salary_comparison_signatures(
    db: AsyncSession,
    months: set[str],
) -> set[tuple[str, str, str, str]]:
    if not months:
        return set()

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415

    result = await db.execute(
        select(
            Salary.month,
            Contact.nom,
            Contact.prenom,
            Salary.gross,
            Salary.net_pay,
        ).join(Contact)
    )
    return {
        _gestion_salary_comparison_signature(
            month=month,
            employee_name=_format_contact_display_name(nom, prenom) or nom,
            gross=Decimal(str(gross)),
            net_pay=Decimal(str(net_pay)),
        )
        for month, nom, prenom, gross, net_pay in result.all()
        if month in months
    }


async def _load_existing_salary_comparison_items(
    db: AsyncSession,
    months: set[str],
) -> dict[tuple[str, str, str, str], dict[str, str]]:
    if not months:
        return {}

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415

    result = await db.execute(
        select(
            Salary.month,
            Contact.nom,
            Contact.prenom,
            Salary.gross,
            Salary.net_pay,
        ).join(Contact)
    )
    details: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for month, nom, prenom, gross, net_pay in result.all():
        if month not in months:
            continue
        employee_name = _format_contact_display_name(nom, prenom) or nom
        signature = _gestion_salary_comparison_signature(
            month=month,
            employee_name=employee_name,
            gross=Decimal(str(gross)),
            net_pay=Decimal(str(net_pay)),
        )
        details[signature] = _make_gestion_salary_extra_detail(
            month=month,
            employee_name=employee_name,
            gross=Decimal(str(gross)),
            net_pay=Decimal(str(net_pay)),
        )
    return details


async def _load_existing_bank_comparison_signatures(
    db: AsyncSession,
    years: set[int],
    start_date: date | None = None,
    end_date: date | None = None,
) -> set[tuple[str, str, str, str]]:
    if not years:
        return set()

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.bank import BankTransaction, BankTransactionSource  # noqa: PLC0415

    result = await db.execute(
        select(
            BankTransaction.date,
            BankTransaction.amount,
            BankTransaction.description,
            BankTransaction.reference,
            BankTransaction.source,
        )
    )
    return {
        _gestion_bank_comparison_signature(
            entry_date=entry_date,
            amount=amount,
            description=description,
            reference=reference,
        )
        for entry_date, amount, description, reference, source in result.all()
        if entry_date.year in years
        and _is_within_date_bounds(entry_date, start_date, end_date)
        and source != BankTransactionSource.SYSTEM_OPENING
    }


async def _load_existing_bank_comparison_items(
    db: AsyncSession,
    years: set[int],
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[tuple[str, str, str, str], dict[str, str]]:
    if not years:
        return {}

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.bank import BankTransaction, BankTransactionSource  # noqa: PLC0415

    result = await db.execute(
        select(
            BankTransaction.date,
            BankTransaction.amount,
            BankTransaction.description,
            BankTransaction.reference,
            BankTransaction.source,
        )
    )
    details: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for entry_date, amount, description, reference, source in result.all():
        if (
            entry_date.year not in years
            or not _is_within_date_bounds(entry_date, start_date, end_date)
            or source == BankTransactionSource.SYSTEM_OPENING
        ):
            continue
        signature = _gestion_bank_comparison_signature(
            entry_date=entry_date,
            amount=amount,
            description=description,
            reference=reference,
        )
        details[signature] = _make_gestion_bank_extra_detail(
            entry_date=entry_date,
            amount=amount,
            description=description,
            reference=reference,
        )
    return details


async def _load_existing_cash_comparison_signatures(
    db: AsyncSession,
    years: set[int],
    start_date: date | None = None,
    end_date: date | None = None,
) -> set[tuple[str, str, str, str, str]]:
    if not years:
        return set()

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.cash import CashEntrySource, CashRegister  # noqa: PLC0415

    result = await db.execute(
        select(
            CashRegister.date,
            CashRegister.type,
            CashRegister.amount,
            CashRegister.description,
            CashRegister.reference,
            CashRegister.source,
        )
    )
    return {
        _gestion_cash_comparison_signature(
            entry_date=entry_date,
            movement_type=str(movement_type),
            amount=amount,
            description=description,
            reference=reference,
        )
        for entry_date, movement_type, amount, description, reference, source in result.all()
        if entry_date.year in years
        and _is_within_date_bounds(entry_date, start_date, end_date)
        and source != CashEntrySource.SYSTEM_OPENING
    }


async def _load_existing_cash_comparison_items(
    db: AsyncSession,
    years: set[int],
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[tuple[str, str, str, str, str], dict[str, str]]:
    if not years:
        return {}

    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.cash import CashEntrySource, CashRegister  # noqa: PLC0415

    result = await db.execute(
        select(
            CashRegister.date,
            CashRegister.type,
            CashRegister.amount,
            CashRegister.description,
            CashRegister.reference,
            CashRegister.source,
        )
    )
    details: dict[tuple[str, str, str, str, str], dict[str, str]] = {}
    for entry_date, movement_type, amount, description, reference, source in result.all():
        if (
            entry_date.year not in years
            or not _is_within_date_bounds(entry_date, start_date, end_date)
            or source == CashEntrySource.SYSTEM_OPENING
        ):
            continue
        signature = _gestion_cash_comparison_signature(
            entry_date=entry_date,
            movement_type=str(movement_type),
            amount=amount,
            description=description,
            reference=reference,
        )
        details[signature] = _make_gestion_cash_extra_detail(
            entry_date=entry_date,
            movement_type=str(movement_type),
            amount=amount,
            description=description,
            reference=reference,
        )
    return details
