"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import._constants import (
    _ImportSheetFailure,
    logger,
)
from backend.services.excel_import._loaders import (
    _load_existing_contacts_by_salary_key,
    _load_existing_salary_keys,
)
from backend.services.excel_import._salary import (
    _salary_employee_key,
    _salary_entry_date,
    _salary_month_group_lines,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_payment_sheet,
    _parse_salary_sheet,
)
from backend.services.excel_import_parsing import (
    format_contact_display_name as _format_contact_display_name,
)
from backend.services.excel_import_payment_matching import (
    resolve_payment_match_with_database as _resolve_payment_match,
)
from backend.services.excel_import_policy import (
    EXISTING_SALARY_MESSAGE,
    format_row_issue,
    make_payment_resolution_issue,
)
from backend.services.excel_import_results import ImportResult
from backend.services.excel_import_types import (
    NormalizedSalaryRow,
    RowIgnoredIssue,
)


async def _import_payments_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import payments from a sheet."""
    from backend.models.invoice import InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    parsed_sheet, normalized_rows, _ = _parse_payment_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    logger.debug(
        "Importing payments sheet — rows=%s missing_columns=%s",
        len(normalized_rows),
        parsed_sheet.missing_columns,
    )

    created_payments: list[tuple[Payment, InvoiceType]] = []
    affected_invoice_ids: set[int] = set()
    for payment_row in normalized_rows:
        pay_date = payment_row.payment_date
        amount = payment_row.amount
        method = payment_row.method

        resolution = await _resolve_payment_match(db, payment_row)
        blocking_issue = make_payment_resolution_issue(
            source_row_number=payment_row.source_row_number,
            status=resolution.status,
            candidate=resolution.candidate,
            message=resolution.message,
            require_persistable_candidate=True,
        )
        if blocking_issue is not None:
            raise ValueError(format_row_issue(blocking_issue))

        candidate = resolution.candidate
        assert candidate is not None
        assert candidate.invoice_id is not None
        invoice_id = candidate.invoice_id
        contact_id = candidate.contact_id
        inv_type = candidate.invoice_type or InvoiceType.CLIENT

        payment = Payment(
            invoice_id=invoice_id,
            contact_id=contact_id,
            date=pay_date,
            amount=amount,
            method=method,
            cheque_number=payment_row.cheque_number,
            deposited=payment_row.deposited,
            deposit_date=payment_row.deposit_date,
        )
        db.add(payment)
        created_payments.append((payment, inv_type))
        affected_invoice_ids.add(invoice_id)
        logger.debug(
            "Row %d — payment %s queued (invoice_id=%d, amount=%s)",
            payment_row.source_row_number,
            pay_date,
            invoice_id,
            amount,
        )
        result.payments_created += 1
        result.add_imported_row(ws.title, "payments")

    try:
        await db.flush()
        for payment, _ in created_payments:
            result.record_created_object(
                sheet_name=ws.title,
                kind="payments",
                object_type="payment",
                object_id=payment.id,
                reference=str(payment.id) if payment.id is not None else None,
                details={
                    "invoice_id": payment.invoice_id,
                    "contact_id": payment.contact_id,
                    "amount": str(payment.amount),
                    "date": payment.date.isoformat(),
                },
            )
        # Refresh invoice statuses and generate accounting entries
        from backend.services.accounting_engine import (
            generate_entries_for_payment,
        )  # noqa: PLC0415
        from backend.services.payment import _refresh_invoice_status  # noqa: PLC0415

        for inv_id in affected_invoice_ids:
            await _refresh_invoice_status(db, inv_id)
        for p, p_inv_type in created_payments:
            try:
                entries = await generate_entries_for_payment(db, p, p_inv_type)
                result.entries_created += len(entries)
            except Exception as e:
                logger.debug("Accounting entries skipped for payment: %s", e)
                result.add_warning(
                    ws.title,
                    "payments",
                    f"Ecritures comptables non generees pour un paiement importe : {e}",
                )
        await db.flush()
        logger.debug(
            "Payments import done — created=%d skipped=%d entries=%d",
            result.payments_created,
            result.skipped,
            result.entries_created,
        )
    except Exception as exc:
        logger.error("Payments flush failed: %s", exc, exc_info=True)
        result.add_import_error("paiements", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_salaries_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import salary records from the historical `Aide Salaires` worksheet."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.accounting_entry import AccountingEntry, EntrySourceType  # noqa: PLC0415
    from backend.models.contact import Contact, ContactType  # noqa: PLC0415
    from backend.models.salary import Salary  # noqa: PLC0415
    from backend.services.accounting_engine import _next_entry_number  # noqa: PLC0415
    from backend.services.fiscal_year_service import find_fiscal_year_id_for_date  # noqa: PLC0415

    parsed_sheet, normalized_rows, _ = _parse_salary_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    existing_contacts_by_salary_key = await _load_existing_contacts_by_salary_key(db)
    existing_salary_keys = await _load_existing_salary_keys(db)
    created_contacts: list[Contact] = []
    created_salaries: list[Salary] = []
    touched_months: set[str] = set()

    for salary_row in normalized_rows:
        employee_key = _salary_employee_key(salary_row.employee_name)
        contact = existing_contacts_by_salary_key.get(employee_key)
        if contact is None:
            contact = Contact(nom=salary_row.employee_name, type=ContactType.FOURNISSEUR)
            db.add(contact)
            await db.flush()
            created_contacts.append(contact)
            existing_contacts_by_salary_key[employee_key] = contact
            result.contacts_created += 1

        salary_key = (salary_row.month, employee_key)
        if salary_key in existing_salary_keys:
            result.add_ignored_row(
                ws.title,
                "salaries",
                format_row_issue(
                    RowIgnoredIssue(
                        source_row_number=salary_row.source_row_number,
                        message=EXISTING_SALARY_MESSAGE,
                    )
                ),
            )
            continue

        salary = Salary(
            employee_id=contact.id,
            month=salary_row.month,
            hours=salary_row.hours,
            gross=salary_row.gross,
            employee_charges=salary_row.employee_charges,
            employer_charges=salary_row.employer_charges,
            tax=salary_row.tax,
            net_pay=salary_row.net_pay,
            notes="Imported from Gestion Excel",
        )
        db.add(salary)
        created_salaries.append(salary)
        existing_salary_keys.add(salary_key)
        touched_months.add(salary_row.month)
        result.salaries_created += 1
        result.add_imported_row(ws.title, "salaries")

    try:
        await db.flush()
        for contact in created_contacts:
            result.record_created_object(
                sheet_name=ws.title,
                kind="salaries",
                object_type="contact",
                object_id=contact.id,
                reference=contact.nom,
                details={"created_from": "salary_sheet"},
            )
        for salary in created_salaries:
            result.record_created_object(
                sheet_name=ws.title,
                kind="salaries",
                object_type="salary",
                object_id=salary.id,
                reference=salary.month,
                details={"employee_id": salary.employee_id, "net_pay": str(salary.net_pay)},
            )

        existing_salary_entry_group_keys = {
            group_key
            for (group_key,) in (
                await db.execute(
                    select(AccountingEntry.group_key).where(
                        AccountingEntry.source_type == EntrySourceType.SALARY,
                        AccountingEntry.group_key.is_not(None),
                    )
                )
            ).all()
            if group_key
        }

        for month in sorted(touched_months):
            month_group_prefix = f"salary-import:{month}:"
            if any(
                group_key.startswith(month_group_prefix)
                for group_key in existing_salary_entry_group_keys
            ):
                continue

            month_result = await db.execute(
                select(
                    Salary.hours,
                    Salary.gross,
                    Salary.employee_charges,
                    Salary.employer_charges,
                    Salary.tax,
                    Salary.net_pay,
                    Contact.nom,
                    Contact.prenom,
                )
                .join(Contact, Contact.id == Salary.employee_id)
                .where(Salary.month == month)
                .order_by(Contact.nom, Contact.prenom, Salary.employee_id)
            )
            month_salary_rows = month_result.all()
            if not month_salary_rows:
                continue

            month_rows = [
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
                for (
                    hours,
                    gross,
                    employee_charges,
                    employer_charges,
                    tax,
                    net_pay,
                    nom,
                    prenom,
                ) in month_salary_rows
            ]
            entry_date = _salary_entry_date(month)
            fiscal_year_id = await find_fiscal_year_id_for_date(db, entry_date)

            for group_kind, group_lines in zip(
                ("accrual", "payment"),
                _salary_month_group_lines(month, month_rows),
                strict=True,
            ):
                group_key = f"salary-import:{month}:{group_kind}"
                for account_number, label, debit, credit in group_lines:
                    if debit <= 0 and credit <= 0:
                        continue
                    entry = AccountingEntry(
                        entry_number=await _next_entry_number(db),
                        date=entry_date,
                        account_number=account_number,
                        label=label,
                        debit=debit,
                        credit=credit,
                        fiscal_year_id=fiscal_year_id,
                        source_type=EntrySourceType.SALARY,
                        source_id=None,
                        group_key=group_key,
                    )
                    db.add(entry)
                    result.entries_created += 1

            existing_salary_entry_group_keys.add(f"salary-import:{month}:accrual")
            existing_salary_entry_group_keys.add(f"salary-import:{month}:payment")

        await db.flush()
        logger.debug("Salaries import done — created=%d", result.salaries_created)
    except Exception as exc:
        logger.error("Salaries flush failed: %s", exc, exc_info=True)
        result.add_import_error("salaires", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc
