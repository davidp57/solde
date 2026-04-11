"""Unit tests for Excel import DB state and idempotence helpers."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.contact import Contact, ContactType
from backend.models.import_log import ImportLog, ImportLogStatus, ImportLogType
from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType
from backend.services.excel_import_results import ImportResult, PreviewResult
from backend.services.excel_import_state import (
    add_comptabilite_coexistence_validation,
    compute_file_hash,
    count_generated_accounting_entries,
    find_successful_import_log,
    load_existing_contact_preview_keys,
    load_existing_invoice_numbers,
    mark_preview_as_already_imported,
    record_import_log,
)


def test_compute_file_hash_is_stable() -> None:
    payload = b"excel-import-payload"

    assert compute_file_hash(payload) == compute_file_hash(payload)
    assert compute_file_hash(payload) != compute_file_hash(b"other-payload")


@pytest.mark.asyncio
async def test_load_existing_preview_keys_and_invoice_numbers(db_session) -> None:
    contact = Contact(nom="Christine", prenom="Lopes", type=ContactType.CLIENT)
    db_session.add(contact)
    await db_session.flush()

    db_session.add(
        Invoice(
            number="2025-0142",
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 8, 1),
            total_amount=Decimal("55.00"),
            paid_amount=Decimal("0.00"),
            status=InvoiceStatus.DRAFT,
        )
    )
    await db_session.commit()

    assert await load_existing_contact_preview_keys(db_session) == {"christine lopes"}
    assert await load_existing_invoice_numbers(db_session) == {"2025-0142"}


@pytest.mark.asyncio
async def test_count_generated_accounting_entries_excludes_manual(db_session) -> None:
    db_session.add_all(
        [
            AccountingEntry(
                entry_number="000001",
                date=date(2025, 1, 1),
                account_number="706000",
                label="Generated invoice",
                debit=Decimal("10.00"),
                credit=Decimal("0.00"),
                source_type=EntrySourceType.INVOICE,
            ),
            AccountingEntry(
                entry_number="000002",
                date=date(2025, 1, 2),
                account_number="512000",
                label="Manual entry",
                debit=Decimal("0.00"),
                credit=Decimal("10.00"),
                source_type=EntrySourceType.MANUAL,
            ),
        ]
    )
    await db_session.commit()

    assert await count_generated_accounting_entries(db_session) == 1


@pytest.mark.asyncio
async def test_add_comptabilite_coexistence_validation_blocks_preview(db_session) -> None:
    db_session.add(
        AccountingEntry(
            entry_number="000001",
            date=date(2025, 1, 1),
            account_number="706000",
            label="Generated invoice",
            debit=Decimal("10.00"),
            credit=Decimal("0.00"),
            source_type=EntrySourceType.INVOICE,
        )
    )
    await db_session.commit()

    preview = PreviewResult()
    await add_comptabilite_coexistence_validation(db_session, preview)

    assert preview.can_import is False
    assert preview.errors == [
        "Import comptabilite bloque : des ecritures auto-generees "
        "issues de la gestion existent deja en base (1)."
    ]


@pytest.mark.asyncio
async def test_record_and_find_successful_import_log(db_session) -> None:
    blocked_result = ImportResult()
    blocked_result.errors.append("blocked")
    await record_import_log(
        db_session,
        import_type=ImportLogType.GESTION,
        status=ImportLogStatus.BLOCKED,
        file_hash="hash-1",
        file_name="Gestion 2025.xlsx",
        result=blocked_result,
    )

    success_result = ImportResult()
    success_result.contacts_created = 2
    await record_import_log(
        db_session,
        import_type=ImportLogType.GESTION,
        status=ImportLogStatus.SUCCESS,
        file_hash="hash-1",
        file_name="Gestion 2025.xlsx",
        result=success_result,
    )
    await db_session.commit()

    found = await find_successful_import_log(db_session, ImportLogType.GESTION, "hash-1")

    assert found is not None
    assert isinstance(found, ImportLog)
    assert found.status == ImportLogStatus.SUCCESS
    assert found.file_name == "Gestion 2025.xlsx"
    assert '"contacts_created": 2' in (found.summary or "")


def test_mark_preview_as_already_imported_formats_message() -> None:
    preview = PreviewResult()

    mark_preview_as_already_imported(
        preview,
        "gestion",
        SimpleNamespace(created_at=datetime(2026, 4, 11, 9, 30, 15)),
    )

    assert preview.can_import is False
    assert preview.errors == ["Fichier deja importe (gestion) le 2026-04-11 09:30:15"]
