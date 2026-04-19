"""Database-backed helpers for Excel import preview, idempotence, and logs."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.excel_import_parsing import normalize_text
from backend.services.excel_import_preview_helpers import contact_preview_key
from backend.services.excel_import_results import ImportResult, PreviewResult


def compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


async def find_successful_import_log(
    db: AsyncSession,
    import_type: str,
    file_hash: str,
) -> Any | None:
    from sqlalchemy import desc, select  # noqa: PLC0415

    from backend.models.import_log import ImportLog, ImportLogStatus  # noqa: PLC0415

    result = await db.execute(
        select(ImportLog)
        .where(
            ImportLog.import_type == import_type,
            ImportLog.file_hash == file_hash,
            ImportLog.status == ImportLogStatus.SUCCESS,
        )
        .order_by(desc(ImportLog.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def load_existing_contact_preview_keys(db: AsyncSession) -> set[str]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415

    result = await db.execute(select(Contact.nom, Contact.prenom))
    return {contact_preview_key(nom or "", prenom) for nom, prenom in result.all() if nom}


async def load_existing_contacts_by_preview_key(db: AsyncSession) -> dict[str, list[Any]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415

    result = await db.execute(select(Contact))
    contacts_by_key: dict[str, list[Any]] = {}
    for contact in result.scalars():
        if not contact.nom:
            continue
        preview_key = contact_preview_key(contact.nom or "", contact.prenom)
        contacts_by_key.setdefault(preview_key, []).append(contact)
    return contacts_by_key


async def load_existing_invoice_numbers(db: AsyncSession) -> set[str]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.invoice import Invoice  # noqa: PLC0415

    result = await db.execute(select(Invoice.number))
    return {normalize_text(number) for (number,) in result.all() if number}


def accounting_entry_signature(
    *,
    entry_date: date,
    account_number: str,
    label: str,
    debit: Decimal,
    credit: Decimal,
) -> str:
    """Build a stable signature for an accounting row used for exact de-duplication."""
    normalized_label = " ".join(label.split())

    def normalize_decimal(value: Decimal) -> str:
        return format(value.quantize(Decimal("0.01")).normalize(), "f")

    return "|".join(
        (
            entry_date.isoformat(),
            normalize_text(account_number.strip()),
            normalize_text(normalized_label),
            normalize_decimal(debit),
            normalize_decimal(credit),
        )
    )


def accounting_entry_line_signature(
    *,
    entry_date: date,
    account_number: str,
    debit: Decimal,
    credit: Decimal,
) -> str:
    """Build a label-agnostic signature for one accounting line."""

    def normalize_decimal(value: Decimal) -> str:
        return format(value.quantize(Decimal("0.01")).normalize(), "f")

    return "|".join(
        (
            entry_date.isoformat(),
            normalize_text(account_number.strip()),
            normalize_decimal(debit),
            normalize_decimal(credit),
        )
    )


def accounting_entry_group_signature(lines: list[str]) -> tuple[str, ...]:
    """Build an order-independent signature for a full accounting operation."""
    return tuple(sorted(lines))


async def load_existing_accounting_entry_signatures(db: AsyncSession) -> set[str]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.accounting_entry import AccountingEntry  # noqa: PLC0415

    result = await db.execute(
        select(
            AccountingEntry.date,
            AccountingEntry.account_number,
            AccountingEntry.label,
            AccountingEntry.debit,
            AccountingEntry.credit,
        )
    )
    return {
        accounting_entry_signature(
            entry_date=entry_date,
            account_number=account_number,
            label=label,
            debit=debit,
            credit=credit,
        )
        for entry_date, account_number, label, debit, credit in result.all()
    }


async def load_existing_manual_accounting_line_signatures(db: AsyncSession) -> set[str]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.accounting_entry import AccountingEntry, EntrySourceType  # noqa: PLC0415

    result = await db.execute(
        select(
            AccountingEntry.date,
            AccountingEntry.account_number,
            AccountingEntry.debit,
            AccountingEntry.credit,
        ).where(AccountingEntry.source_type == EntrySourceType.MANUAL)
    )
    return {
        accounting_entry_line_signature(
            entry_date=entry_date,
            account_number=account_number,
            debit=debit,
            credit=credit,
        )
        for entry_date, account_number, debit, credit in result.all()
    }


async def load_existing_generated_accounting_group_signatures(
    db: AsyncSession,
) -> set[tuple[str, ...]]:
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.accounting_entry import AccountingEntry  # noqa: PLC0415

    result = await db.execute(
        select(
            AccountingEntry.id,
            AccountingEntry.date,
            AccountingEntry.account_number,
            AccountingEntry.debit,
            AccountingEntry.credit,
            AccountingEntry.source_type,
            AccountingEntry.source_id,
            AccountingEntry.group_key,
        ).where(AccountingEntry.source_type != "manual")
    )

    grouped_lines: dict[str, list[str]] = defaultdict(list)
    for (
        entry_id,
        entry_date,
        account_number,
        debit,
        credit,
        source_type,
        source_id,
        group_key,
    ) in result.all():
        runtime_group_key = group_key or (
            f"{source_type}:{source_id}"
            if source_type is not None and source_id is not None
            else f"entry:{entry_id}"
        )
        grouped_lines[runtime_group_key].append(
            accounting_entry_line_signature(
                entry_date=entry_date,
                account_number=account_number,
                debit=debit,
                credit=credit,
            )
        )

    return {accounting_entry_group_signature(lines) for lines in grouped_lines.values()}


async def count_generated_accounting_entries(db: AsyncSession) -> int:
    from sqlalchemy import func, select  # noqa: PLC0415

    from backend.models.accounting_entry import (  # noqa: PLC0415
        AccountingEntry,
        EntrySourceType,
    )

    generated_sources = (
        EntrySourceType.INVOICE,
        EntrySourceType.PAYMENT,
        EntrySourceType.DEPOSIT,
        EntrySourceType.SALARY,
        EntrySourceType.GESTION,
        EntrySourceType.CLOTURE,
    )
    result = await db.execute(
        select(func.count(AccountingEntry.id)).where(
            AccountingEntry.source_type.in_(generated_sources)
        )
    )
    return int(result.scalar_one() or 0)


async def add_comptabilite_coexistence_validation(db: AsyncSession, preview: PreviewResult) -> None:
    generated_entries_count = await count_generated_accounting_entries(db)
    if generated_entries_count <= 0:
        return

    message = (
        "Import comptabilite : des ecritures auto-generees issues de la gestion "
        f"existent deja en base ({generated_entries_count}). "
        "Les doublons exacts du journal seront ignores et seules les ecritures "
        "nouvelles seront importees."
    )
    preview.warnings.append(message)


async def record_import_log(
    db: AsyncSession,
    *,
    import_type: str,
    status: str,
    file_hash: str,
    file_name: str | None,
    result: ImportResult,
) -> None:
    from backend.models.import_log import ImportLog  # noqa: PLC0415

    db.add(
        ImportLog(
            import_type=import_type,
            status=status,
            file_hash=file_hash,
            file_name=file_name,
            summary=json.dumps(result.to_log_dict(), ensure_ascii=False),
        )
    )
    await db.flush()


def mark_preview_as_already_imported(
    preview: PreviewResult, import_type: str, import_log: Any
) -> None:
    imported_at = getattr(import_log, "created_at", None)
    imported_at_text = imported_at.isoformat(sep=" ", timespec="seconds") if imported_at else ""
    message = f"Fichier deja importe ({import_type})"
    if imported_at_text:
        message = f"{message} le {imported_at_text}"
    preview.errors.append(message)
    preview.can_import = False
