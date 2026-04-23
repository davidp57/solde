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
from backend.services.excel_import._invoices import _build_client_invoice_lines_from_import_row
from backend.services.excel_import._sheet_wrappers import (
    _parse_contact_sheet,
    _parse_invoice_sheet,
)
from backend.services.excel_import_parsing import (
    format_contact_display_name as _format_contact_display_name,
)
from backend.services.excel_import_parsing import (
    normalize_text as _normalize_text,
)
from backend.services.excel_import_parsing import (
    split_contact_full_name as _split_contact_full_name,
)
from backend.services.excel_import_policy import (
    filter_duplicate_contact_rows,
    filter_duplicate_invoice_rows,
    format_row_issue,
    make_existing_contact_issue,
    make_existing_invoice_issue,
    resolve_invoice_contact_match,
)
from backend.services.excel_import_preview_helpers import (
    contact_preview_key as _contact_preview_key,
)
from backend.services.excel_import_results import ImportResult
from backend.services.excel_import_state import (
    load_existing_contacts_by_preview_key as _load_existing_contacts_by_preview_key,
)
from backend.services.invoice import apply_default_due_date


async def _import_contacts_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import contacts from a sheet."""
    from backend.models.contact import Contact, ContactType  # noqa: PLC0415

    parsed_sheet, normalized_rows, _ = _parse_contact_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    created_contacts: list[Contact] = []
    existing_contacts_by_preview_key = await _load_existing_contacts_by_preview_key(db)
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
        preview_key = _contact_preview_key(contact_row.nom, contact_row.prenom)
        if existing_contacts_by_preview_key.get(preview_key):
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
        existing_contacts_by_preview_key.setdefault(preview_key, []).append(contact)
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
                reference=_format_contact_display_name(contact.nom, contact.prenom),
            )
        logger.debug("Contacts import done — created=%d", result.contacts_created)
    except Exception as exc:
        logger.error("Contacts flush failed: %s", exc, exc_info=True)
        result.add_import_error("contacts", exc)
        await db.rollback()
        raise _ImportSheetFailure from exc


async def _import_invoices_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import invoices from a sheet with flexible column detection."""
    from sqlalchemy import select  # noqa: PLC0415
    from sqlalchemy.orm import selectinload  # noqa: PLC0415

    from backend.models.contact import Contact, ContactType  # noqa: PLC0415
    from backend.models.invoice import (  # noqa: PLC0415
        Invoice,
        InvoiceLine,
        InvoiceStatus,
        InvoiceType,
        derive_client_invoice_label,
    )

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_invoice_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    logger.debug(
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
    default_invoice_due_days = await settings_service.get_default_invoice_due_days(db)
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
            contact_nom, contact_prenom = _split_contact_full_name(invoice_row.contact_name)
            new_contact = Contact(
                nom=contact_nom,
                prenom=contact_prenom,
                type=ContactType.CLIENT,
            )
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

        invoice_lines = _build_client_invoice_lines_from_import_row(invoice_row)
        derived_label = derive_client_invoice_label(
            {line["line_type"] for line in invoice_lines if line["amount"] > 0}
        )

        invoice = Invoice(
            number=number_raw,
            type=InvoiceType.CLIENT,
            contact_id=contact_id,
            date=invoice_date,
            due_date=apply_default_due_date(invoice_date, None, default_invoice_due_days),
            total_amount=total,
            paid_amount=Decimal("0"),
            status=InvoiceStatus.SENT,
            label=derived_label,
            has_explicit_breakdown=len(invoice_lines) > 1,
        )
        db.add(invoice)
        await db.flush()
        db.add_all(
            [
                InvoiceLine(
                    invoice_id=invoice.id,
                    description=line["description"],
                    line_type=line["line_type"],
                    quantity=Decimal("1"),
                    unit_price=line["amount"],
                    amount=line["amount"],
                )
                for line in invoice_lines
            ]
        )
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
                reference=_format_contact_display_name(contact.nom, contact.prenom),
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
                refreshed_invoice = (
                    (
                        await db.execute(
                            select(Invoice)
                            .where(Invoice.id == inv_obj.id)
                            .options(selectinload(Invoice.lines))
                        )
                    )
                    .scalars()
                    .one()
                )
                entries = await generate_entries_for_invoice(db, refreshed_invoice)
                result.entries_created += len(entries)
            except Exception as e:
                logger.debug("Accounting entries skipped for invoice '%s': %s", inv_obj.number, e)
                result.add_warning(
                    ws.title,
                    "invoices",
                    f"Ecritures comptables non generees pour la facture {inv_obj.number} : {e}",
                )
        logger.debug(
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
