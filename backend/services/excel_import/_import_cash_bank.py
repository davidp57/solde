"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services import settings as settings_service
from backend.services.excel_import._constants import (
    _ImportSheetFailure,
    logger,
)
from backend.services.excel_import._entry_groups import (
    _ensure_supplier_invoice_payment,
    _queue_client_payment_from_bank_row,
    _supplier_invoice_candidate_from_bank_row,
    _supplier_invoice_candidate_from_cash_row,
)
from backend.services.excel_import._loaders import (
    _generate_direct_bank_entries,
    _load_existing_payment_signatures,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_bank_sheet,
    _parse_cash_sheet,
)
from backend.services.excel_import_policy import (
    format_row_issue,
)
from backend.services.excel_import_results import ImportResult
from backend.services.excel_import_state import (
    load_existing_contacts_by_preview_key as _load_existing_contacts_by_preview_key,
)
from backend.services.excel_import_types import (
    NormalizedBankRow,
)


async def _import_cash_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import cash register movements from a 'Caisse' sheet.

    Expected columns (flexible): date | libellé/description | entrée | sortie
    or: date | description | montant | type (E/S or in/out)
    """
    from backend.models.cash import CashEntrySource, CashMovementType, CashRegister  # noqa: PLC0415
    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_invoice,
        generate_entries_for_payment,
    )
    from backend.services.cash_service import recompute_cash_balances  # noqa: PLC0415
    from backend.services.payment import _refresh_invoice_status  # noqa: PLC0415

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_cash_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        logger.debug(
            "Cash sheet skipped — header not detected or missing columns=%s",
            parsed_sheet.missing_columns if parsed_sheet else None,
        )
        return

    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "cash",
            format_row_issue(ignored_issue),
        )

    created_cash_entries: list[CashRegister] = []
    created_supplier_invoice_ids: set[int] = set()
    created_supplier_payment_ids: list[int] = []
    affected_invoice_ids: set[int] = set()
    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    default_invoice_due_days = await settings_service.get_default_invoice_due_days(db)
    for cash_row in normalized_rows:
        contact_id: int | None = None
        payment_id: int | None = None
        supplier_candidate = _supplier_invoice_candidate_from_cash_row(cash_row)
        if supplier_candidate is not None:
            (
                invoice_id,
                payment_id,
                contact_id,
                created_invoice,
            ) = await _ensure_supplier_invoice_payment(
                db,
                candidate=supplier_candidate,
                existing_contacts_by_preview_key=existing_contacts_by_preview_key,
                result=result,
                sheet_name=ws.title,
                default_invoice_due_days=default_invoice_due_days,
            )
            affected_invoice_ids.add(invoice_id)
            created_supplier_payment_ids.append(payment_id)
            if created_invoice:
                created_supplier_invoice_ids.add(invoice_id)
        entry = CashRegister(
            date=cash_row.entry_date,
            amount=cash_row.amount,
            type=CashMovementType(cash_row.movement_type),
            contact_id=contact_id,
            payment_id=payment_id,
            reference=cash_row.reference,
            description=cash_row.description,
            source=CashEntrySource.MANUAL,
            balance_after=Decimal("0"),
        )
        db.add(entry)
        created_cash_entries.append(entry)
        result.cash_created += 1
        result.add_imported_row(ws.title, "cash")

    try:
        await db.flush()
        if created_cash_entries:
            await recompute_cash_balances(db)
        for entry in created_cash_entries:
            result.record_created_object(
                sheet_name=ws.title,
                kind="cash",
                object_type="cash_register",
                object_id=entry.id,
                reference=entry.date.isoformat(),
                details={
                    "amount": str(entry.amount),
                    "type": str(entry.type),
                    "description": entry.description,
                },
            )
        for invoice_id in created_supplier_invoice_ids:
            invoice = await db.get(Invoice, invoice_id)
            if invoice is None:
                continue
            result.entries_created += len(await generate_entries_for_invoice(db, invoice))
        for invoice_id in affected_invoice_ids:
            await _refresh_invoice_status(db, invoice_id)
        for payment_id in created_supplier_payment_ids:
            supplier_payment = await db.get(Payment, payment_id)
            if supplier_payment is None:
                continue
            result.entries_created += len(
                await generate_entries_for_payment(db, supplier_payment, InvoiceType.FOURNISSEUR)
            )
        await db.flush()
        logger.debug("Cash import done — created=%d", result.cash_created)
    except Exception as exc:
        logger.error("Cash flush failed: %s", exc, exc_info=True)
        result.add_import_error("caisse", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_bank_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import bank transactions from a 'Banque' or 'Relevé' sheet.

    Expected columns (flexible): date | libellé | débit | crédit | solde
    or: date | description | montant (positive=credit, negative=debit)
    """
    from backend.models.bank import (
        BankTransaction,
        BankTransactionSource,
    )  # noqa: PLC0415
    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415
    from backend.services.accounting_engine import (  # noqa: PLC0415
        generate_entries_for_invoice,
        generate_entries_for_payment,
    )
    from backend.services.payment import _refresh_invoice_status  # noqa: PLC0415

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_bank_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        logger.debug(
            "Bank sheet skipped — header not detected or missing columns=%s",
            parsed_sheet.missing_columns if parsed_sheet else None,
        )
        return

    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "bank",
            format_row_issue(ignored_issue),
        )

    created_bank_entries: list[tuple[BankTransaction, NormalizedBankRow]] = []
    created_payments: list[tuple[Payment, InvoiceType]] = []
    created_supplier_invoice_ids: set[int] = set()
    created_supplier_payment_ids: list[int] = []
    affected_invoice_ids: set[int] = set()
    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    existing_payment_signatures = await _load_existing_payment_signatures(db)
    default_invoice_due_days = await settings_service.get_default_invoice_due_days(db)
    for bank_row in normalized_rows:
        supplier_candidate = _supplier_invoice_candidate_from_bank_row(bank_row)
        if supplier_candidate is not None:
            invoice_id, payment_id, _, created_invoice = await _ensure_supplier_invoice_payment(
                db,
                candidate=supplier_candidate,
                existing_contacts_by_preview_key=existing_contacts_by_preview_key,
                result=result,
                sheet_name=ws.title,
                default_invoice_due_days=default_invoice_due_days,
            )
            affected_invoice_ids.add(invoice_id)
            created_supplier_payment_ids.append(payment_id)
            if created_invoice:
                created_supplier_invoice_ids.add(invoice_id)
        else:
            await _queue_client_payment_from_bank_row(
                db,
                bank_row=bank_row,
                existing_payment_signatures=existing_payment_signatures,
                created_payments=created_payments,
                affected_invoice_ids=affected_invoice_ids,
                result=result,
                sheet_name=ws.title,
            )
        entry = BankTransaction(
            date=bank_row.entry_date,
            amount=bank_row.amount,
            reference=bank_row.reference,
            description=bank_row.description,
            balance_after=bank_row.balance_after,
            source=BankTransactionSource.IMPORT,
        )
        db.add(entry)
        created_bank_entries.append((entry, bank_row))
        result.bank_created += 1
        result.add_imported_row(ws.title, "bank")

    try:
        await db.flush()
        for payment, _ in created_payments:
            result.record_created_object(
                sheet_name=ws.title,
                kind="payments",
                object_type="payment",
                object_id=payment.id,
                reference=payment.reference,
                details={
                    "invoice_id": payment.invoice_id,
                    "contact_id": payment.contact_id,
                    "amount": str(payment.amount),
                    "date": payment.date.isoformat(),
                },
            )
        for entry, _ in created_bank_entries:
            result.record_created_object(
                sheet_name=ws.title,
                kind="bank",
                object_type="bank_transaction",
                object_id=entry.id,
                reference=entry.date.isoformat(),
                details={
                    "amount": str(entry.amount),
                    "description": entry.description,
                    "balance_after": str(entry.balance_after),
                },
            )
        for entry, bank_row in created_bank_entries:
            result.entries_created += len(
                await _generate_direct_bank_entries(
                    db,
                    bank_row=bank_row,
                    bank_entry=entry,
                )
            )
        for invoice_id in created_supplier_invoice_ids:
            invoice = await db.get(Invoice, invoice_id)
            if invoice is None:
                continue
            result.entries_created += len(await generate_entries_for_invoice(db, invoice))
        for invoice_id in affected_invoice_ids:
            await _refresh_invoice_status(db, invoice_id)
        for payment_id in created_supplier_payment_ids:
            supplier_payment = await db.get(Payment, payment_id)
            if supplier_payment is None:
                continue
            result.entries_created += len(
                await generate_entries_for_payment(db, supplier_payment, InvoiceType.FOURNISSEUR)
            )
        for payment, invoice_type in created_payments:
            result.entries_created += len(
                await generate_entries_for_payment(db, payment, invoice_type)
            )
        await db.flush()
        logger.debug("Bank import done — created=%d", result.bank_created)
    except Exception as exc:
        logger.error("Bank flush failed: %s", exc, exc_info=True)
        result.add_import_error("banque", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc
