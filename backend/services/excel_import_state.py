"""Database-backed helpers for Excel import preview, idempotence, and logs."""

from __future__ import annotations

import hashlib
import json
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
    return {
        contact_preview_key(nom or "", prenom)
        for nom, prenom in result.all()
        if nom
    }


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
        EntrySourceType.CLOTURE,
    )
    result = await db.execute(
        select(func.count(AccountingEntry.id)).where(
            AccountingEntry.source_type.in_(generated_sources)
        )
    )
    return int(result.scalar_one() or 0)


async def add_comptabilite_coexistence_validation(
    db: AsyncSession, preview: PreviewResult
) -> None:
    generated_entries_count = await count_generated_accounting_entries(db)
    if generated_entries_count <= 0:
        return

    message = (
        "Import comptabilite bloque : des ecritures auto-generees issues de la gestion "
        f"existent deja en base ({generated_entries_count})."
    )
    preview.errors.append(message)
    preview.can_import = False


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
