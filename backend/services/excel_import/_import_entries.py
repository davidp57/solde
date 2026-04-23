"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import._constants import (
    _CLIENT_INVOICE_CLARIFIED_MESSAGE,
    _ImportSheetFailure,
    _load_existing_generated_accounting_group_signatures,
    logger,
)
from backend.services.excel_import._entry_groups import (
    _build_entry_row_groups,
    _matching_existing_salary_entry_group,
    _normalized_entry_group_signature,
)
from backend.services.excel_import._invoices import (
    _clarify_existing_client_invoice_from_entries,
    _load_existing_client_invoices_by_number,
    _load_existing_client_payment_reference_signatures,
    _load_existing_supplier_payment_reference_signatures,
    _matching_existing_client_invoice_reference,
    _matching_existing_client_payment_reference,
    _matching_existing_supplier_invoice_payment_reference,
    _merge_existing_client_invoice_entry_groups,
)
from backend.services.excel_import._loaders import _load_existing_salary_group_signatures
from backend.services.excel_import._sheet_wrappers import _parse_entries_sheet
from backend.services.excel_import_policy import (
    ENTRY_COVERED_BY_SOLDE_MESSAGE,
    ENTRY_EXISTING_MESSAGE,
    ENTRY_NEAR_EXISTING_MANUAL_MESSAGE,
    format_row_issue,
)
from backend.services.excel_import_results import ImportResult
from backend.services.excel_import_state import (
    accounting_entry_line_signature as _accounting_entry_line_signature,
)
from backend.services.excel_import_state import (
    accounting_entry_signature as _accounting_entry_signature,
)
from backend.services.excel_import_state import (
    load_existing_accounting_entry_signatures as _load_existing_accounting_entry_signatures,
)
from backend.services.excel_import_state import (
    load_existing_invoice_numbers as _load_existing_invoice_numbers,
)
from backend.services.excel_import_state import (
    load_existing_manual_accounting_line_signatures,
)
from backend.services.excel_import_types import (
    RowIgnoredIssue,
    RowWarningIssue,
)


async def _import_entries_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import accounting entries from a comptabilité sheet."""
    from sqlalchemy import func, select  # noqa: PLC0415

    from backend.models.accounting_entry import (
        AccountingEntry,
        EntrySourceType,
    )  # noqa: PLC0415
    from backend.services.fiscal_year_service import find_fiscal_year_id_for_date  # noqa: PLC0415

    parsed_sheet, normalized_rows, _, ignored_issues = _parse_entries_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    existing_entry_signatures = await _load_existing_accounting_entry_signatures(db)
    existing_invoice_numbers = await _load_existing_invoice_numbers(db)
    existing_client_invoices_by_number = await _load_existing_client_invoices_by_number(db)
    existing_client_payment_signatures = await _load_existing_client_payment_reference_signatures(
        db
    )
    existing_supplier_payment_signatures = (
        await _load_existing_supplier_payment_reference_signatures(db)
    )
    existing_salary_group_signatures = await _load_existing_salary_group_signatures(db)
    existing_manual_line_signatures = await load_existing_manual_accounting_line_signatures(db)
    existing_generated_group_signatures = (
        await _load_existing_generated_accounting_group_signatures(db)
    )
    for ignored_issue in ignored_issues:
        result.add_ignored_row(
            ws.title,
            "entries",
            format_row_issue(ignored_issue),
        )

    # Pre-compute next entry number using MAX to avoid duplicates after deletions
    max_result = await db.execute(select(func.max(AccountingEntry.entry_number)))
    current_max: str | None = max_result.scalar_one_or_none()
    try:
        next_entry_num = int(current_max) + 1 if current_max is not None else 1
    except ValueError:
        next_entry_num = 1
    entries_to_add: list[AccountingEntry] = []
    entry_groups = _build_entry_row_groups(normalized_rows)
    index = 0
    while index < len(entry_groups):
        entry_group, next_index = _merge_existing_client_invoice_entry_groups(
            entry_groups,
            index,
            existing_invoice_numbers,
        )
        existing_client_invoice_reference = _matching_existing_client_invoice_reference(
            entry_group,
            existing_invoice_numbers,
        )
        if existing_client_invoice_reference is not None:
            clarified_invoice = await _clarify_existing_client_invoice_from_entries(
                db,
                entry_group,
                existing_client_invoices_by_number,
            )
            message = (
                _CLIENT_INVOICE_CLARIFIED_MESSAGE
                if clarified_invoice is not None
                else ENTRY_COVERED_BY_SOLDE_MESSAGE
            )
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=message,
                        )
                    ),
                )
            if clarified_invoice is not None:
                result.record_created_object(
                    sheet_name=ws.title,
                    kind="entries",
                    object_type="invoice",
                    object_id=clarified_invoice.id,
                    reference=clarified_invoice.number,
                    details={"action": "clarified_from_accounting_entries"},
                )
            index = next_index
            continue

        if _matching_existing_client_payment_reference(
            entry_group,
            existing_client_payment_signatures,
        ):
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_COVERED_BY_SOLDE_MESSAGE,
                        )
                    ),
                )
            index = next_index
            continue

        if _matching_existing_supplier_invoice_payment_reference(
            entry_group,
            existing_supplier_payment_signatures,
        ):
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_COVERED_BY_SOLDE_MESSAGE,
                        )
                    ),
                )
            index = next_index
            continue

        if _matching_existing_salary_entry_group(
            entry_group,
            existing_salary_group_signatures,
        ):
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_COVERED_BY_SOLDE_MESSAGE,
                        )
                    ),
                )
            index = next_index
            continue

        if _normalized_entry_group_signature(entry_group) in existing_generated_group_signatures:
            for entry_row in entry_group:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_COVERED_BY_SOLDE_MESSAGE,
                        )
                    ),
                )
            index = next_index
            continue

        group_key = f"import:{uuid4().hex}"
        for entry_row in entry_group:
            signature = _accounting_entry_signature(
                entry_date=entry_row.entry_date,
                account_number=entry_row.account_number,
                label=entry_row.label,
                debit=entry_row.debit,
                credit=entry_row.credit,
            )
            if signature in existing_entry_signatures:
                result.add_ignored_row(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowIgnoredIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_EXISTING_MESSAGE,
                        )
                    ),
                )
                continue

            line_signature = _accounting_entry_line_signature(
                entry_date=entry_row.entry_date,
                account_number=entry_row.account_number,
                debit=entry_row.debit,
                credit=entry_row.credit,
            )
            if line_signature in existing_manual_line_signatures:
                result.add_warning(
                    ws.title,
                    "entries",
                    format_row_issue(
                        RowWarningIssue(
                            source_row_number=entry_row.source_row_number,
                            message=ENTRY_NEAR_EXISTING_MANUAL_MESSAGE,
                        )
                    ),
                )

            entry = AccountingEntry(
                entry_number=f"{next_entry_num:06d}",
                date=entry_row.entry_date,
                account_number=entry_row.account_number,
                label=entry_row.label,
                debit=entry_row.debit,
                credit=entry_row.credit,
                fiscal_year_id=await find_fiscal_year_id_for_date(db, entry_row.entry_date),
                source_type=EntrySourceType.MANUAL,
                group_key=group_key,
            )
            entries_to_add.append(entry)
            next_entry_num += 1
            existing_entry_signatures.add(signature)
            result.add_imported_row(ws.title, "entries")

        index = next_index

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
        logger.debug("Entries import done — created=%d", result.entries_created)
    except Exception as exc:
        logger.error("Entries flush failed: %s", exc, exc_info=True)
        result.add_import_error("écritures", exc)
        await db.rollback()
        raise _ImportSheetFailure(str(exc), sheet_name=ws.title) from exc
