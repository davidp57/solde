"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import_classification import (
    classify_comptabilite_sheet as _classify_comptabilite_sheet,
)
from backend.services.excel_import_classification import (
    classify_gestion_sheet as _classify_gestion_sheet,
)
from backend.services.excel_import_classification import (
    sheet_has_content as _sheet_has_content,
)
from backend.services.excel_import_parsers import (
    parse_bank_sheet as _parse_bank_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_cash_sheet as _parse_cash_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_contact_sheet as _parse_contact_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_entries_sheet as _parse_entries_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_invoice_sheet as _parse_invoice_sheet_impl,
)
from backend.services.excel_import_parsers import (
    parse_payment_sheet as _parse_payment_sheet_impl,
)
from backend.services.excel_import_parsing import (
    normalize_text as _normalize_text,
)
from backend.services.excel_import_parsing import (
    parse_str as _parse_str,
)
from backend.services.excel_import_payment_matching import (
    PaymentMatchCandidate,
)
from backend.services.excel_import_payment_matching import (
    make_workbook_invoice_candidate as _make_workbook_invoice_candidate,
)
from backend.services.excel_import_payment_matching import (
    resolve_payment_match_with_database as _resolve_payment_match,
)
from backend.services.excel_import_policy import (
    COMPTABILITE_UNKNOWN_STRUCTURE_MESSAGE,
    GESTION_UNKNOWN_STRUCTURE_MESSAGE,
    detect_gestion_preview_header,
    filter_duplicate_contact_rows,
    filter_duplicate_invoice_rows,
    find_ambiguous_invoice_contact_issues,
    find_existing_contact_issues,
    find_existing_invoice_issues,
    format_row_issue,
    make_existing_contact_issue,
    make_existing_invoice_issue,
    make_payment_resolution_issue,
    preview_warning_for_comptabilite_reason,
    preview_warning_for_gestion_reason,
    resolve_invoice_contact_match,
    should_ignore_cash_pending_deposit_forecast,
)
from backend.services.excel_import_preview_helpers import (
    append_finalized_sheet_preview as _append_finalized_sheet_preview,
)
from backend.services.excel_import_preview_helpers import (
    append_ignored_issues as _append_ignored_issues,
)
from backend.services.excel_import_preview_helpers import (
    append_preview_blocked_issue as _append_preview_blocked_issue,
)
from backend.services.excel_import_preview_helpers import (
    append_preview_ignored_issue as _append_preview_ignored_issue,
)
from backend.services.excel_import_preview_helpers import (
    append_preview_open_error as _append_preview_open_error,
)
from backend.services.excel_import_preview_helpers import (
    append_reasoned_ignored_sheet_preview as _append_reasoned_ignored_sheet_preview,
)
from backend.services.excel_import_preview_helpers import (
    append_row_issues as _append_row_issues,
)
from backend.services.excel_import_preview_helpers import (
    append_unknown_structure_sheet_preview as _append_unknown_structure_sheet_preview,
)
from backend.services.excel_import_preview_helpers import (
    contact_preview_key as _contact_preview_key,
)
from backend.services.excel_import_preview_helpers import (
    finalize_preview_can_import as _finalize_preview_can_import,
)
from backend.services.excel_import_preview_helpers import (
    find_sheet_preview as _find_sheet_preview,
)
from backend.services.excel_import_preview_helpers import (
    recompute_preview_can_import as _recompute_preview_can_import,
)
from backend.services.excel_import_preview_helpers import (
    register_preview_contact as _register_preview_contact,
)
from backend.services.excel_import_results import ImportResult, PreviewResult
from backend.services.excel_import_sheet_helpers import (
    detect_header_row as _detect_header_row,
)
from backend.services.excel_import_sheet_helpers import (
    get_row_value as _get_row_value,
)
from backend.services.excel_import_state import (
    add_comptabilite_coexistence_validation as _add_comptabilite_coexistence_validation,
)
from backend.services.excel_import_state import (
    compute_file_hash as _compute_file_hash,
)
from backend.services.excel_import_state import (
    find_successful_import_log as _find_successful_import_log,
)
from backend.services.excel_import_state import (
    load_existing_contacts_by_preview_key as _load_existing_contacts_by_preview_key,
)
from backend.services.excel_import_state import (
    load_existing_invoice_numbers as _load_existing_invoice_numbers,
)
from backend.services.excel_import_state import (
    mark_preview_as_already_imported as _mark_preview_as_already_imported,
)
from backend.services.excel_import_state import (
    record_import_log as _record_import_log,
)
from backend.services.excel_import_types import (
    NormalizedBankRow,
    NormalizedCashRow,
    NormalizedContactRow,
    NormalizedEntryRow,
    NormalizedInvoiceRow,
    NormalizedPaymentRow,
    ParsedSheet,
    RowIgnoredIssue,
    RowValidationIssue,
)

logger = logging.getLogger(__name__)

_GESTION_IMPORT_ORDER = ("contacts", "invoices", "payments", "cash", "bank")


class _ImportSheetFailure(RuntimeError):
    """Internal marker used to abort the global import after a sheet-local failure."""


# ---------------------------------------------------------------------------
# Main import functions
# ---------------------------------------------------------------------------


async def import_gestion_file(
    db: AsyncSession, file_bytes: bytes, file_name: str | None = None
) -> ImportResult:
    """Import contacts, invoices and payments from a 'Gestion YYYY.xlsx' file.

    Expected sheets:
    - 'Factures' or 'Clients' : contact, date, montant, type, statut
    - 'Paiements' : date, contact, montant, mode, N° chèque

    The parser blocks recognized sheets containing invalid rows or unresolved payments.
    """
    import openpyxl  # noqa: PLC0415

    result = ImportResult()

    file_hash = _compute_file_hash(file_bytes)
    preview = await preview_gestion_file(db, file_bytes)
    if preview.errors:
        result.absorb_preview(preview)
        await _record_import_log(
            db,
            import_type="gestion",
            status="blocked",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    try:
        from io import BytesIO  # noqa: PLC0415

        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        result.add_open_file_error(exc)
        await _record_import_log(
            db,
            import_type="gestion",
            status="failed",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    sheets_by_kind: dict[str, list[Any]] = {kind: [] for kind in _GESTION_IMPORT_ORDER}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        kind, _ = _classify_gestion_sheet(sheet_name)
        if kind in sheets_by_kind:
            sheets_by_kind[kind].append(ws)

    for kind in _GESTION_IMPORT_ORDER:
        try:
            for ws in sheets_by_kind[kind]:
                if kind == "invoices":
                    await _import_invoices_sheet(db, ws, result)
                elif kind == "payments":
                    await _import_payments_sheet(db, ws, result)
                elif kind == "contacts":
                    await _import_contacts_sheet(db, ws, result)
                elif kind == "cash":
                    await _import_cash_sheet(db, ws, result)
                elif kind == "bank":
                    await _import_bank_sheet(db, ws, result)
        except Exception as exc:
            logger.error("Gestion import aborted during %s: %s", kind, exc, exc_info=True)
            await db.rollback()
            result.reset_persisted_counts()
            if not isinstance(exc, _ImportSheetFailure):
                result.add_import_error("gestion", exc)
            await _record_import_log(
                db,
                import_type="gestion",
                status="failed",
                file_hash=file_hash,
                file_name=file_name,
                result=result,
            )
            return result

    await _record_import_log(
        db,
        import_type="gestion",
        status="success",
        file_hash=file_hash,
        file_name=file_name,
        result=result,
    )
    return result


async def import_comptabilite_file(
    db: AsyncSession, file_bytes: bytes, file_name: str | None = None
) -> ImportResult:
    """Import accounting entries from a 'Comptabilité YYYY.xlsx' file.

    Expected sheet columns (flexible column detection):
    date | N° pièce | compte | libellé | débit | crédit
    """
    import openpyxl  # noqa: PLC0415

    result = ImportResult()

    file_hash = _compute_file_hash(file_bytes)
    preview = await preview_comptabilite_file(db, file_bytes)
    if preview.errors:
        result.absorb_preview(preview)
        await _record_import_log(
            db,
            import_type="comptabilite",
            status="blocked",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    try:
        from io import BytesIO  # noqa: PLC0415

        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        result.add_open_file_error(exc)
        await _record_import_log(
            db,
            import_type="comptabilite",
            status="failed",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    try:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            kind, _ = _classify_comptabilite_sheet(sheet_name)
            if kind == "entries":
                await _import_entries_sheet(db, ws, result)
    except Exception as exc:
        logger.error("Comptabilite import aborted: %s", exc, exc_info=True)
        await db.rollback()
        result.reset_persisted_counts()
        if not isinstance(exc, _ImportSheetFailure):
            result.add_import_error("comptabilite", exc)
        await _record_import_log(
            db,
            import_type="comptabilite",
            status="failed",
            file_hash=file_hash,
            file_name=file_name,
            result=result,
        )
        return result

    await _record_import_log(
        db,
        import_type="comptabilite",
        status="success",
        file_hash=file_hash,
        file_name=file_name,
        result=result,
    )
    return result


def _is_cash_pending_deposit_forecast(
    row: tuple[Any, ...],
    *,
    tiers_idx: int | None,
    libelle_idx: int | None,
    raw_amount: Decimal | None,
) -> bool:
    """Recognize a cash-to-bank forecast row that should be ignored until dated."""
    return should_ignore_cash_pending_deposit_forecast(
        row,
        tiers_idx=tiers_idx,
        libelle_idx=libelle_idx,
        raw_amount=raw_amount,
        get_row_value=_get_row_value,
        parse_str=_parse_str,
        normalize_text=_normalize_text,
    )


def _parse_invoice_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedInvoiceRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    return _parse_invoice_sheet_impl(ws)


def _parse_payment_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedPaymentRow], list[RowValidationIssue]]:
    return _parse_payment_sheet_impl(ws)


def _parse_contact_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedContactRow], list[RowValidationIssue]]:
    return _parse_contact_sheet_impl(ws)


def _parse_cash_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedCashRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    return _parse_cash_sheet_impl(ws)


def _parse_bank_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedBankRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    return _parse_bank_sheet_impl(ws)


def _parse_entries_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedEntryRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    return _parse_entries_sheet_impl(ws)


async def _import_contacts_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import contacts from a sheet."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact, ContactType  # noqa: PLC0415

    parsed_sheet, normalized_rows, _ = _parse_contact_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    created_contacts: list[Contact] = []
    normalized_rows, ignored_issues = filter_duplicate_contact_rows(
        normalized_rows,
        normalize_text=_normalize_text,
    )
    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "contacts",
            format_row_issue(ignored_issue),
        )

    for contact_row in normalized_rows:
        # Idempotency: skip if contact with same nom+prenom exists
        existing = await db.execute(
            select(Contact).where(
                Contact.nom == contact_row.nom,
                Contact.prenom == contact_row.prenom,
            )
        )
        if existing.scalars().first() is not None:
            ignored_issue = make_existing_contact_issue(contact_row.source_row_number)
            result.add_ignored_row(
                ws.title,
                "contacts",
                format_row_issue(ignored_issue),
            )
            continue

        contact = Contact(
            nom=contact_row.nom,
            prenom=contact_row.prenom,
            email=contact_row.email,
            type=ContactType.CLIENT,
        )
        db.add(contact)
        created_contacts.append(contact)
        result.contacts_created += 1
        result.add_imported_row(ws.title, "contacts")

    try:
        await db.flush()
        for contact in created_contacts:
            result.record_created_object(
                sheet_name=ws.title,
                kind="contacts",
                object_type="contact",
                object_id=contact.id,
                reference=f"{contact.nom} {contact.prenom or ''}".strip(),
            )
        logger.info("Contacts import done — created=%d", result.contacts_created)
    except Exception as exc:
        logger.error("Contacts flush failed: %s", exc, exc_info=True)
        result.add_import_error("contacts", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_invoices_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import invoices from a sheet with flexible column detection."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact, ContactType  # noqa: PLC0415
    from backend.models.invoice import (  # noqa: PLC0415
        Invoice,
        InvoiceLabel,
        InvoiceStatus,
        InvoiceType,
    )

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_invoice_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    logger.info(
        "Importing invoices sheet — rows=%s missing_columns=%s",
        len(normalized_rows),
        parsed_sheet.missing_columns,
    )

    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "invoices",
            format_row_issue(ignored_issue),
        )

    normalized_rows, ignored_issues = filter_duplicate_invoice_rows(
        normalized_rows,
        normalize_text=_normalize_text,
    )
    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "invoices",
            format_row_issue(ignored_issue),
        )

    created_invoices: list[Invoice] = []
    created_contacts: list[Contact] = []
    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    generated_number_index = 0
    for invoice_row in normalized_rows:
        invoice_date = invoice_row.invoice_date
        total = invoice_row.amount

        # Find or create contact
        contact_id: int | None = None
        contact_key = _normalize_text(invoice_row.contact_name)
        matched_contact, contact_issue = resolve_invoice_contact_match(
            invoice_row,
            existing_contacts_by_preview_key,
            normalize_text=_normalize_text,
        )
        if contact_issue is not None:
            raise ValueError(format_row_issue(contact_issue))
        if matched_contact is not None:
            contact_id = matched_contact.id
        else:
            new_contact = Contact(nom=invoice_row.contact_name, type=ContactType.CLIENT)
            db.add(new_contact)
            await db.flush()
            created_contacts.append(new_contact)
            contact_id = new_contact.id
            existing_contacts_by_preview_key.setdefault(contact_key, []).append(new_contact)
            result.contacts_created += 1
            logger.debug(
                "Row %d — created contact '%s' (id=%s)",
                invoice_row.source_row_number,
                invoice_row.contact_name,
                contact_id,
            )
        if contact_id is None:
            result.skipped += 1
            continue

        number_raw = invoice_row.invoice_number or ""
        if not number_raw:
            generated_number_index += 1
            number_raw = f"IMP-{invoice_date.year}-{generated_number_index:04d}"

        # Idempotency: skip if already in DB
        existing_inv = await db.execute(select(Invoice).where(Invoice.number == number_raw))
        if existing_inv.scalar_one_or_none() is not None:
            ignored_issue = make_existing_invoice_issue(invoice_row.source_row_number)
            logger.debug(
                "Row %d — invoice '%s' already exists, skipping",
                invoice_row.source_row_number,
                number_raw,
            )
            result.add_ignored_row(
                ws.title,
                "invoices",
                format_row_issue(ignored_issue),
            )
            continue

        invoice = Invoice(
            number=number_raw,
            type=InvoiceType.CLIENT,
            contact_id=contact_id,
            date=invoice_date,
            total_amount=total,
            paid_amount=Decimal("0"),
            status=InvoiceStatus.SENT,
            label=InvoiceLabel(invoice_row.label),
        )
        db.add(invoice)
        created_invoices.append(invoice)
        logger.debug(
            "Row %d — invoice '%s' queued (contact_id=%d, amount=%s)",
            invoice_row.source_row_number,
            number_raw,
            contact_id,
            total,
        )
        result.invoices_created += 1
        result.add_imported_row(ws.title, "invoices")

    try:
        await db.flush()
        for contact in created_contacts:
            result.record_created_object(
                sheet_name=ws.title,
                kind="contacts",
                object_type="contact",
                object_id=contact.id,
                reference=contact.nom,
                details={"created_from": "invoice_sheet"},
            )
        for inv_obj in created_invoices:
            result.record_created_object(
                sheet_name=ws.title,
                kind="invoices",
                object_type="invoice",
                object_id=inv_obj.id,
                reference=inv_obj.number,
                details={"contact_id": inv_obj.contact_id},
            )
        # Generate accounting entries for each new invoice (no-op if no rules configured)
        from backend.services.accounting_engine import (
            generate_entries_for_invoice,
        )  # noqa: PLC0415

        for inv_obj in created_invoices:
            try:
                entries = await generate_entries_for_invoice(db, inv_obj)
                result.entries_created += len(entries)
            except Exception as e:
                logger.warning("Accounting entries skipped for invoice '%s': %s", inv_obj.number, e)
                result.add_warning(
                    ws.title,
                    "invoices",
                    f"Ecritures comptables non generees pour la facture {inv_obj.number} : {e}",
                )
        logger.info(
            "Invoices import done — created=%d skipped=%d entries=%d",
            result.invoices_created,
            result.skipped,
            result.entries_created,
        )
    except Exception as exc:
        logger.error("Invoices flush failed: %s", exc, exc_info=True)
        result.add_import_error("factures", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_payments_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import payments from a sheet."""
    from backend.models.invoice import InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    parsed_sheet, normalized_rows, _ = _parse_payment_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    logger.info(
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
                logger.warning("Accounting entries skipped for payment: %s", e)
                result.add_warning(
                    ws.title,
                    "payments",
                    f"Ecritures comptables non generees pour un paiement importe : {e}",
                )
        await db.flush()
        logger.info(
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


async def _import_cash_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import cash register movements from a 'Caisse' sheet.

    Expected columns (flexible): date | libellé/description | entrée | sortie
    or: date | description | montant | type (E/S or in/out)
    """
    from backend.models.cash import CashMovementType, CashRegister  # noqa: PLC0415

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_cash_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        logger.info(
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
    for cash_row in normalized_rows:
        entry = CashRegister(
            date=cash_row.entry_date,
            amount=cash_row.amount,
            type=CashMovementType(cash_row.movement_type),
            description=cash_row.description,
            balance_after=Decimal("0"),
        )
        db.add(entry)
        created_cash_entries.append(entry)
        result.cash_created += 1
        result.add_imported_row(ws.title, "cash")

    try:
        await db.flush()
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
        logger.info("Cash import done — created=%d", result.cash_created)
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

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_bank_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        logger.info(
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

    created_bank_entries: list[BankTransaction] = []
    for bank_row in normalized_rows:
        entry = BankTransaction(
            date=bank_row.entry_date,
            amount=bank_row.amount,
            description=bank_row.description,
            balance_after=bank_row.balance_after,
            source=BankTransactionSource.IMPORT,
        )
        db.add(entry)
        created_bank_entries.append(entry)
        result.bank_created += 1
        result.add_imported_row(ws.title, "bank")

    try:
        await db.flush()
        for entry in created_bank_entries:
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
        logger.info("Bank import done — created=%d", result.bank_created)
    except Exception as exc:
        logger.error("Bank flush failed: %s", exc, exc_info=True)
        result.add_import_error("banque", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_entries_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import accounting entries from a comptabilité sheet."""
    from sqlalchemy import func, select  # noqa: PLC0415

    from backend.models.accounting_entry import (
        AccountingEntry,
        EntrySourceType,
    )  # noqa: PLC0415

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_entries_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "entries",
            format_row_issue(ignored_issue),
        )

    # Pre-compute next entry number offset to avoid per-row DB queries
    count_result = await db.execute(select(func.count(AccountingEntry.id)))
    base_count = count_result.scalar_one_or_none() or 0
    entries_to_add: list[AccountingEntry] = []
    for local_offset, entry_row in enumerate(normalized_rows, start=1):
        entry = AccountingEntry(
            entry_number=f"{base_count + local_offset:06d}",
            date=entry_row.entry_date,
            account_number=entry_row.account_number,
            label=entry_row.label,
            debit=entry_row.debit,
            credit=entry_row.credit,
            source_type=EntrySourceType.MANUAL,
        )
        entries_to_add.append(entry)
        result.add_imported_row(ws.title, "entries")

    try:
        for entry in entries_to_add:
            db.add(entry)
        await db.flush()
        for entry in entries_to_add:
            result.record_created_object(
                sheet_name=ws.title,
                kind="entries",
                object_type="accounting_entry",
                object_id=entry.id,
                reference=entry.entry_number,
                details={
                    "account_number": entry.account_number,
                    "date": entry.date.isoformat(),
                },
            )
        result.entries_created += len(entries_to_add)
        logger.info("Entries import done — created=%d", result.entries_created)
    except Exception as exc:
        logger.error("Entries flush failed: %s", exc, exc_info=True)
        result.add_import_error("écritures", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _add_gestion_existing_rows_preview(
    db: AsyncSession, file_bytes: bytes, preview: PreviewResult
) -> None:
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
    existing_contact_keys = set(existing_contacts_by_preview_key)
    existing_invoice_numbers = await _load_existing_invoice_numbers(db)

    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        kind, _ = _classify_gestion_sheet(sheet_name)
        sheet_preview = _find_sheet_preview(preview, sheet_name)
        if kind is None or sheet_preview is None or sheet_preview["status"] != "recognized":
            continue

        if kind == "contacts":
            parsed_sheet, contact_rows, _ = _parse_contact_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            contact_rows, _ = filter_duplicate_contact_rows(
                contact_rows,
                normalize_text=_normalize_text,
            )
            ignored_issues = find_existing_contact_issues(
                contact_rows,
                existing_contact_keys,
                contact_preview_key=_contact_preview_key,
            )
            for ignored_issue in ignored_issues:
                _append_preview_ignored_issue(
                    preview,
                    sheet_preview,
                    ignored_issue,
                )
            ignored_count = len(ignored_issues)
            if ignored_count:
                sheet_preview["rows"] = max(0, sheet_preview["rows"] - ignored_count)

        elif kind == "invoices":
            parsed_sheet, invoice_rows, _, _ = _parse_invoice_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            invoice_rows, _ = filter_duplicate_invoice_rows(
                invoice_rows,
                normalize_text=_normalize_text,
            )
            ignored_issues = find_existing_invoice_issues(
                invoice_rows,
                existing_invoice_numbers,
                normalize_text=_normalize_text,
            )
            blocked_issues = find_ambiguous_invoice_contact_issues(
                invoice_rows,
                existing_contacts_by_preview_key,
                normalize_text=_normalize_text,
            )
            for ignored_issue in ignored_issues:
                _append_preview_ignored_issue(
                    preview,
                    sheet_preview,
                    ignored_issue,
                )
            for blocked_issue in blocked_issues:
                _append_preview_blocked_issue(
                    preview,
                    sheet_preview,
                    blocked_issue,
                )
            ignored_count = len(ignored_issues)
            blocked_count = len(blocked_issues)
            if ignored_count:
                sheet_preview["rows"] = max(0, sheet_preview["rows"] - ignored_count)
                preview.estimated_invoices = max(0, preview.estimated_invoices - ignored_count)
            if blocked_count:
                sheet_preview["rows"] = max(0, sheet_preview["rows"] - blocked_count)
                preview.estimated_invoices = max(0, preview.estimated_invoices - blocked_count)

    preview._candidate_contacts.difference_update(existing_contact_keys)
    preview.estimated_contacts = len(preview._candidate_contacts)
    _recompute_preview_can_import(preview)


async def _add_gestion_payment_validation(
    db: AsyncSession, file_bytes: bytes, preview: PreviewResult
) -> None:
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    workbook_candidates: list[PaymentMatchCandidate] = []
    payment_rows_by_sheet: dict[str, list[NormalizedPaymentRow]] = {}

    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        kind, _ = _classify_gestion_sheet(sheet_name)
        if kind == "invoices":
            parsed_sheet, invoice_rows, _, _ = _parse_invoice_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            workbook_candidates.extend(
                _make_workbook_invoice_candidate(invoice_row) for invoice_row in invoice_rows
            )
        elif kind == "payments":
            parsed_sheet, payment_rows, _ = _parse_payment_sheet(ws)
            if parsed_sheet is None or parsed_sheet.missing_columns:
                continue
            payment_rows_by_sheet[sheet_name] = payment_rows

    for sheet_name, payment_rows in payment_rows_by_sheet.items():
        sheet_preview = _find_sheet_preview(preview, sheet_name)
        if sheet_preview is None:
            continue

        payment_errors: list[str] = []
        for payment_row in payment_rows:
            resolution = await _resolve_payment_match(
                db,
                payment_row,
                workbook_candidates,
            )
            blocking_issue = make_payment_resolution_issue(
                source_row_number=payment_row.source_row_number,
                status=resolution.status,
                candidate=resolution.candidate,
                message=resolution.message,
                require_persistable_candidate=False,
            )
            if blocking_issue is not None:
                payment_errors.append(format_row_issue(blocking_issue))

        if payment_errors:
            sheet_preview["errors"].extend(payment_errors)
            preview.errors.extend(f"{sheet_name} — {error}" for error in payment_errors)


def _collect_sample_rows(
    ws: Any, header_row: int, col_map: dict[str, int], *, limit: int = 3
) -> list[dict[str, str]]:
    samples: list[dict[str, str]] = []
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if all(cell is None for cell in row):
            continue
        samples.append(
            {key: _parse_str(row[idx] if idx < len(row) else None) for key, idx in col_map.items()}
        )
        if len(samples) >= limit:
            break
    return samples


def _preview_sheet_gestion(ws: Any, sheet_name: str, preview: PreviewResult) -> None:
    """Count parseable rows and report diagnostics for gestion files."""
    kind, reason = _classify_gestion_sheet(sheet_name)
    if kind is None:
        _append_reasoned_ignored_sheet_preview(
            preview,
            sheet_name=sheet_name,
            has_content=_sheet_has_content(ws),
            warning=preview_warning_for_gestion_reason(reason),
        )
        return

    header_info = detect_gestion_preview_header(
        ws,
        kind,
        detect_header_row=_detect_header_row,
    )

    if header_info is None:
        _append_unknown_structure_sheet_preview(
            preview,
            sheet_name=sheet_name,
            kind=kind,
            warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
        )
        return

    header_row, col_map = header_info
    detected_columns = list(col_map.keys())
    count = 0
    missing_columns: list[str] = []
    ignored_rows = 0
    errors: list[str] = []
    warnings: list[str] = []

    if kind == "contacts":
        parsed_sheet, contact_rows, row_issues = _parse_contact_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        contact_rows, ignored_issues = filter_duplicate_contact_rows(
            contact_rows,
            normalize_text=_normalize_text,
        )
        ignored_rows = len(ignored_issues)
        count = len(contact_rows)
        _append_row_issues(errors, row_issues)
        _append_ignored_issues(warnings, ignored_issues)
        if not missing_columns:
            for contact_row in contact_rows:
                _register_preview_contact(
                    preview,
                    f"{contact_row.nom} {contact_row.prenom or ''}".strip(),
                )
    elif kind == "invoices":
        parsed_sheet, invoice_rows, row_issues, ignored_issues = _parse_invoice_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        invoice_rows, duplicate_ignored_issues = filter_duplicate_invoice_rows(
            invoice_rows,
            normalize_text=_normalize_text,
        )
        ignored_rows = len(ignored_issues) + len(duplicate_ignored_issues)
        count = len(invoice_rows)
        _append_row_issues(errors, row_issues)
        _append_ignored_issues(warnings, ignored_issues)
        _append_ignored_issues(warnings, duplicate_ignored_issues)
        if not missing_columns:
            for invoice_row in invoice_rows:
                _register_preview_contact(preview, invoice_row.contact_name)
            preview.estimated_invoices += count
    elif kind == "payments":
        parsed_sheet, payment_rows, row_issues = _parse_payment_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(payment_rows)
        _append_row_issues(errors, row_issues)
        if not missing_columns:
            for payment_row in payment_rows:
                if payment_row.contact_name:
                    _register_preview_contact(preview, payment_row.contact_name)
            preview.estimated_payments += count
    elif kind == "bank":
        parsed_sheet, bank_rows, row_issues, ignored_issues = _parse_bank_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(bank_rows)
        _append_row_issues(errors, row_issues)
        ignored_rows = len(ignored_issues)
        _append_ignored_issues(warnings, ignored_issues)
    elif kind == "cash":
        parsed_sheet, cash_rows, row_issues, ignored_issues = _parse_cash_sheet(ws)
        if parsed_sheet is None:
            _append_unknown_structure_sheet_preview(
                preview,
                sheet_name=sheet_name,
                kind=kind,
                warning=GESTION_UNKNOWN_STRUCTURE_MESSAGE,
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(cash_rows)
        _append_row_issues(errors, row_issues)
        ignored_rows = len(ignored_issues)
        _append_ignored_issues(warnings, ignored_issues)

    assert parsed_sheet is not None
    col_map = parsed_sheet.col_map
    _append_finalized_sheet_preview(
        preview,
        sheet_name=sheet_name,
        kind=kind,
        header_row=header_row,
        rows=count,
        detected_columns=detected_columns,
        missing_columns=missing_columns,
        ignored_rows=ignored_rows,
        sample_rows=_collect_sample_rows(ws, header_row, col_map),
        warnings=warnings,
        errors=errors,
    )


def _preview_sheet_comptabilite(ws: Any, sheet_name: str, preview: PreviewResult) -> None:
    """Count parseable accounting entry rows and report diagnostics."""
    kind, reason = _classify_comptabilite_sheet(sheet_name)
    if kind is None:
        _append_reasoned_ignored_sheet_preview(
            preview,
            sheet_name=sheet_name,
            has_content=_sheet_has_content(ws),
            warning=preview_warning_for_comptabilite_reason(reason),
        )
        return

    parsed_sheet, normalized_rows, row_issues, ignored_issues = _parse_entries_sheet(ws)
    if parsed_sheet is None:
        _append_unknown_structure_sheet_preview(
            preview,
            sheet_name=sheet_name,
            kind=kind,
            warning=COMPTABILITE_UNKNOWN_STRUCTURE_MESSAGE,
        )
        return

    header_row = parsed_sheet.header_row
    detected_columns = list(parsed_sheet.col_map.keys())
    missing_columns = parsed_sheet.missing_columns
    count = len(normalized_rows)
    warnings: list[str] = []
    errors: list[str] = []
    _append_row_issues(errors, row_issues)
    _append_ignored_issues(warnings, ignored_issues)
    if not missing_columns:
        preview.estimated_entries += count

    _append_finalized_sheet_preview(
        preview,
        sheet_name=sheet_name,
        kind=kind,
        header_row=header_row,
        rows=count,
        detected_columns=detected_columns,
        missing_columns=missing_columns,
        ignored_rows=len(ignored_issues),
        sample_rows=_collect_sample_rows(ws, header_row, parsed_sheet.col_map),
        warnings=warnings,
        errors=errors,
    )


def _preview_gestion_file(file_bytes: bytes) -> PreviewResult:
    """Dry-run parse of a Gestion file using file-only validation."""
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    preview = PreviewResult()
    try:
        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        _append_preview_open_error(preview, exc)
        return preview

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        _preview_sheet_gestion(ws, sheet_name, preview)

    return preview


async def preview_gestion_file(db: AsyncSession, file_bytes: bytes) -> PreviewResult:
    """Dry-run parse of a Gestion file with shared business validation."""
    preview = _preview_gestion_file(file_bytes)
    if preview.errors:
        preview.can_import = False
        return preview

    await _add_gestion_existing_rows_preview(db, file_bytes, preview)

    import_log = await _find_successful_import_log(db, "gestion", _compute_file_hash(file_bytes))
    if import_log is not None:
        _mark_preview_as_already_imported(preview, "gestion", import_log)
        return preview

    await _add_gestion_payment_validation(db, file_bytes, preview)
    _finalize_preview_can_import(preview)
    return preview


async def preview_comptabilite_file(db: AsyncSession, file_bytes: bytes) -> PreviewResult:
    """Dry-run parse of a Comptabilité file — no DB writes."""
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    preview = PreviewResult()
    try:
        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        _append_preview_open_error(preview, exc)
        return preview

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        _preview_sheet_comptabilite(ws, sheet_name, preview)

    await _add_comptabilite_coexistence_validation(db, preview)
    if preview.errors:
        preview.can_import = False
        return preview

    import_log = await _find_successful_import_log(
        db, "comptabilite", _compute_file_hash(file_bytes)
    )
    if import_log is not None:
        _mark_preview_as_already_imported(preview, "comptabilite", import_log)
        return preview

    _finalize_preview_can_import(preview)

    return preview
