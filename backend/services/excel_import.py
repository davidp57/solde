"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class ImportResult:
    """Summary of an import operation."""

    def __init__(self) -> None:
        self.contacts_created: int = 0
        self.invoices_created: int = 0
        self.payments_created: int = 0
        self.entries_created: int = 0
        self.skipped: int = 0
        self.errors: list[str] = []

    def to_dict(self) -> dict:
        return {
            "contacts_created": self.contacts_created,
            "invoices_created": self.invoices_created,
            "payments_created": self.payments_created,
            "entries_created": self.entries_created,
            "skipped": self.skipped,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Excel parsing helpers
# ---------------------------------------------------------------------------


def _parse_decimal(value: Any) -> Decimal | None:
    """Parse a cell value into Decimal, returning None if not valid."""
    if value is None or value == "":
        return None
    try:
        # Handle French locale: "1 234,56" → "1234.56"
        cleaned = str(value).strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_date(value: Any) -> date | None:
    """Parse a cell value into date."""
    if value is None or value == "":
        return None
    if isinstance(value, (date, datetime)):
        return value.date() if isinstance(value, datetime) else value
    s = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_str(value: Any, max_len: int | None = None) -> str:
    """Parse a cell value into str, optionally truncated."""
    if value is None:
        return ""
    s = str(value).strip()
    if max_len:
        s = s[:max_len]
    return s


def _normalize_payment_method(value: Any) -> str:
    """Map French payment method labels to system values."""
    s = _parse_str(value).lower()
    if "vir" in s:
        return "virement"
    if "chq" in s or "chèq" in s or "che" in s:
        return "cheque"
    if "esp" in s or "cash" in s:
        return "especes"
    return "virement"


# ---------------------------------------------------------------------------
# Main import functions
# ---------------------------------------------------------------------------


async def import_gestion_file(db: AsyncSession, file_bytes: bytes) -> ImportResult:
    """Import contacts, invoices and payments from a 'Gestion YYYY.xlsx' file.

    Expected sheets:
    - 'Factures' or 'Clients' : contact, date, montant, type, statut
    - 'Paiements' : date, contact, montant, mode, N° chèque

    The parser is lenient — unknown columns are ignored, missing values are skipped.
    """
    import openpyxl  # noqa: PLC0415

    result = ImportResult()

    try:
        from io import BytesIO  # noqa: PLC0415

        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        result.errors.append(f"Impossible d'ouvrir le fichier : {exc}")
        return result

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        sheet_lower = sheet_name.lower()

        if any(k in sheet_lower for k in ("fact", "client", "adh")):
            await _import_invoices_sheet(db, ws, result)
        elif any(k in sheet_lower for k in ("paie", "règl", "encaiss")):
            await _import_payments_sheet(db, ws, result)
        elif any(k in sheet_lower for k in ("contact", "fourniss")):
            await _import_contacts_sheet(db, ws, result)

    return result


async def import_comptabilite_file(db: AsyncSession, file_bytes: bytes) -> ImportResult:
    """Import accounting entries from a 'Comptabilité YYYY.xlsx' file.

    Expected sheet columns (flexible column detection):
    date | N° pièce | compte | libellé | débit | crédit
    """
    import openpyxl  # noqa: PLC0415

    result = ImportResult()

    try:
        from io import BytesIO  # noqa: PLC0415

        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        result.errors.append(f"Impossible d'ouvrir le fichier : {exc}")
        return result

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        sheet_lower = sheet_name.lower()
        if any(k in sheet_lower for k in ("journal", "ecrit", "écriture", "compt")):
            await _import_entries_sheet(db, ws, result)

    return result


# ---------------------------------------------------------------------------
# Sheet-level parsers
# ---------------------------------------------------------------------------


def _detect_header_row(ws: Any, keywords: list[str]) -> tuple[int, dict[str, int]] | None:
    """Find the header row and return (row_index, {col_name: col_index})."""
    for row_idx, row in enumerate(ws.iter_rows(max_row=20, values_only=True), start=1):
        row_lower = [_parse_str(c).lower() for c in row]
        matched = sum(1 for kw in keywords if any(kw in cell for cell in row_lower))
        if matched >= 2:
            col_map: dict[str, int] = {}
            for col_idx, cell in enumerate(row_lower):
                col_map[cell] = col_idx
            return row_idx, col_map
    return None


async def _import_contacts_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import contacts from a sheet."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact, ContactType  # noqa: PLC0415

    header_info = _detect_header_row(ws, ["nom", "prenom"])
    if header_info is None:
        result.skipped += 1
        return

    header_row, col_map = header_info

    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        nom_idx = next((col_map[k] for k in col_map if "nom" in k and "prenom" not in k), None)
        prenom_idx = next((col_map[k] for k in col_map if "prenom" in k or "prénom" in k), None)
        email_idx = next((col_map[k] for k in col_map if "email" in k or "mail" in k), None)

        nom = _parse_str(row[nom_idx]) if nom_idx is not None and nom_idx < len(row) else ""
        if not nom:
            continue

        prenom = (
            _parse_str(row[prenom_idx]) if prenom_idx is not None and prenom_idx < len(row) else ""
        )
        email = (
            _parse_str(row[email_idx]) if email_idx is not None and email_idx < len(row) else None
        )

        # Idempotency: skip if contact with same nom+prenom exists
        existing = await db.execute(
            select(Contact).where(Contact.nom == nom, Contact.prenom == (prenom or None))
        )
        if existing.scalar_one_or_none() is not None:
            result.skipped += 1
            continue

        contact = Contact(
            nom=nom,
            prenom=prenom or None,
            email=email or None,
            type=ContactType.CLIENT,
        )
        db.add(contact)
        result.contacts_created += 1

    try:
        await db.flush()
        logger.info("Contacts import done — created=%d", result.contacts_created)
    except Exception as exc:
        logger.error("Contacts flush failed: %s", exc, exc_info=True)
        result.errors.append(f"Erreur import contacts : {exc}")
        await db.rollback()


async def _import_invoices_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import invoices from a sheet with flexible column detection."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.invoice import (  # noqa: PLC0415
        Invoice,
        InvoiceLabel,
        InvoiceStatus,
        InvoiceType,
    )

    header_info = _detect_header_row(ws, ["montant", "date"])
    if header_info is None:
        result.skipped += 1
        return

    header_row, col_map = header_info

    # Map column positions
    date_idx = next((col_map[k] for k in col_map if "date" in k), None)
    montant_idx = next((col_map[k] for k in col_map if "montant" in k or "total" in k), None)
    nom_idx = next((col_map[k] for k in col_map if "nom" in k), None)
    # Exclude the date column from number detection to avoid date values as invoice numbers
    numero_idx = next(
        (
            col_map[k]
            for k in col_map
            if ("num" in k or "n°" in k or "facture" in k) and col_map[k] != date_idx
        ),
        None,
    )

    if montant_idx is None:
        logger.warning("Sheet skipped — no 'montant' column found")
        result.skipped += 1
        return

    logger.info(
        "Importing invoices sheet — date_idx=%s num_idx=%s montant_idx=%s nom_idx=%s",
        date_idx,
        numero_idx,
        montant_idx,
        nom_idx,
    )

    # Regex to detect values that look like a date (not a valid invoice number)
    _date_pattern = re.compile(
        r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$|^\d{2}/\d{2}/\d{4}$|^\d{2}-\d{2}-\d{4}$"
    )

    row_count = 0
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if all(c is None for c in row):
            continue

        invoice_date = (
            _parse_date(row[date_idx]) if date_idx is not None and date_idx < len(row) else None
        )
        if invoice_date is None:
            invoice_date = date.today()

        total = _parse_decimal(row[montant_idx] if montant_idx < len(row) else None)
        if total is None or total <= 0:
            logger.debug(
                "Row %d skipped — invalid amount: %s",
                row_count + 1,
                row[montant_idx] if montant_idx < len(row) else None,
            )
            result.skipped += 1
            continue

        # Find contact — skip row if not found (no hardcoded fallback)
        contact_id: int | None = None
        if nom_idx is not None and nom_idx < len(row):
            nom = _parse_str(row[nom_idx])
            if nom:
                existing = await db.execute(select(Contact).where(Contact.nom.ilike(f"%{nom}%")))
                c = existing.scalar_one_or_none()
                if c:
                    contact_id = c.id
                else:
                    logger.debug("Row %d — contact '%s' not found, skipping", row_count + 1, nom)
        if contact_id is None:
            result.skipped += 1
            continue

        # Build invoice number — reject date-like values
        number_raw = ""
        if numero_idx is not None and numero_idx < len(row):
            raw_cell = row[numero_idx]
            if not isinstance(raw_cell, (date, datetime)):
                candidate = _parse_str(raw_cell)
                if candidate and not _date_pattern.match(candidate):
                    number_raw = candidate
                else:
                    logger.debug(
                        "Row %d — cell value '%s' looks like a date, ignoring as number",
                        row_count + 1,
                        raw_cell,
                    )
        if not number_raw:
            number_raw = f"IMP-{invoice_date.year}-{row_count + 1:04d}"

        # Idempotency
        existing_inv = await db.execute(select(Invoice).where(Invoice.number == number_raw))
        if existing_inv.scalar_one_or_none() is not None:
            logger.debug(
                "Row %d — invoice '%s' already exists, skipping", row_count + 1, number_raw
            )
            result.skipped += 1
            continue

        invoice = Invoice(
            number=number_raw,
            type=InvoiceType.CLIENT,
            contact_id=contact_id,
            date=invoice_date,
            total_amount=total,
            paid_amount=Decimal("0"),
            status=InvoiceStatus.SENT,
            label=InvoiceLabel.GENERAL,
        )
        db.add(invoice)
        logger.debug(
            "Row %d — invoice '%s' queued (contact_id=%d, amount=%s)",
            row_count + 1,
            number_raw,
            contact_id,
            total,
        )
        result.invoices_created += 1
        row_count += 1

    try:
        await db.flush()
        logger.info(
            "Invoices import done — created=%d skipped=%d", result.invoices_created, result.skipped
        )
    except Exception as exc:
        logger.error("Invoices flush failed: %s", exc, exc_info=True)
        result.errors.append(f"Erreur import factures : {exc}")
        await db.rollback()


async def _import_payments_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import payments from a sheet."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.invoice import Invoice  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    header_info = _detect_header_row(ws, ["montant", "date"])
    if header_info is None:
        result.skipped += 1
        return

    header_row, col_map = header_info

    date_idx = next((col_map[k] for k in col_map if "date" in k), None)
    montant_idx = next((col_map[k] for k in col_map if "montant" in k), None)
    mode_idx = next((col_map[k] for k in col_map if "mode" in k or "règl" in k), None)
    invoice_idx = next((col_map[k] for k in col_map if "facture" in k or "num" in k), None)
    nom_idx = next((col_map[k] for k in col_map if "nom" in k), None)

    if montant_idx is None:
        result.skipped += 1
        return

    logger.info(
        "Importing payments sheet — date_idx=%s montant_idx=%s invoice_idx=%s nom_idx=%s",
        date_idx,
        montant_idx,
        invoice_idx,
        nom_idx,
    )

    row_num = 0
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        row_num += 1
        if all(c is None for c in row):
            continue

        pay_date = (
            _parse_date(row[date_idx]) if date_idx is not None and date_idx < len(row) else None
        )
        if pay_date is None:
            pay_date = date.today()

        amount = _parse_decimal(row[montant_idx] if montant_idx < len(row) else None)
        if amount is None or amount <= 0:
            continue

        method = _normalize_payment_method(
            row[mode_idx] if mode_idx is not None and mode_idx < len(row) else None
        )

        # Try to find matching invoice
        invoice_ref = (
            _parse_str(row[invoice_idx])
            if invoice_idx is not None and invoice_idx < len(row)
            else ""
        )
        invoice_id: int | None = None
        contact_id: int | None = None

        if invoice_ref:
            inv_result = await db.execute(
                select(Invoice).where(Invoice.number.ilike(f"%{invoice_ref}%"))
            )
            inv = inv_result.scalar_one_or_none()
            if inv:
                invoice_id = inv.id
                contact_id = inv.contact_id

        # Fallback: find contact by name and pick their latest invoice
        if invoice_id is None and nom_idx is not None and nom_idx < len(row):
            nom = _parse_str(row[nom_idx])
            if nom:
                c_result = await db.execute(select(Contact).where(Contact.nom.ilike(f"%{nom}%")))
                c = c_result.scalar_one_or_none()
                if c:
                    contact_id = c.id
                    inv_result2 = await db.execute(
                        select(Invoice)
                        .where(Invoice.contact_id == c.id)
                        .order_by(Invoice.date.desc())
                        .limit(1)
                    )
                    inv2 = inv_result2.scalar_one_or_none()
                    if inv2:
                        invoice_id = inv2.id

        if invoice_id is None or contact_id is None:
            logger.debug(
                "Row %d — payment skipped: no matching invoice/contact ref='%s'",
                row_num,
                invoice_ref,
            )
            result.skipped += 1
            continue

        payment = Payment(
            invoice_id=invoice_id,
            contact_id=contact_id,
            date=pay_date,
            amount=amount,
            method=method,
            deposited=False,
        )
        db.add(payment)
        logger.debug(
            "Row %d — payment %s queued (invoice_id=%d, amount=%s)",
            row_num,
            pay_date,
            invoice_id,
            amount,
        )
        result.payments_created += 1

    try:
        await db.flush()
        logger.info(
            "Payments import done — created=%d skipped=%d", result.payments_created, result.skipped
        )
    except Exception as exc:
        logger.error("Payments flush failed: %s", exc, exc_info=True)
        result.errors.append(f"Erreur import paiements : {exc}")
        await db.rollback()


async def _import_entries_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import accounting entries from a comptabilité sheet."""
    from sqlalchemy import func, select  # noqa: PLC0415

    from backend.models.accounting_entry import AccountingEntry, EntrySourceType  # noqa: PLC0415

    header_info = _detect_header_row(ws, ["compte", "débit"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["compte", "credit"])
    if header_info is None:
        result.skipped += 1
        return

    header_row, col_map = header_info

    date_idx = next((col_map[k] for k in col_map if "date" in k), None)
    compte_idx = next((col_map[k] for k in col_map if "compte" in k), None)
    libelle_idx = next((col_map[k] for k in col_map if "libel" in k or "label" in k), None)
    debit_idx = next((col_map[k] for k in col_map if "débit" in k or "debit" in k), None)
    credit_idx = next((col_map[k] for k in col_map if "crédit" in k or "credit" in k), None)

    if compte_idx is None or (debit_idx is None and credit_idx is None):
        result.skipped += 1
        return

    # Pre-compute next entry number offset to avoid per-row DB queries
    count_result = await db.execute(select(func.count(AccountingEntry.id)))
    base_count = count_result.scalar_one_or_none() or 0
    local_offset = 0

    entries_to_add: list[AccountingEntry] = []
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if all(c is None for c in row):
            continue

        entry_date = (
            _parse_date(row[date_idx]) if date_idx is not None and date_idx < len(row) else None
        )
        if entry_date is None:
            entry_date = date.today()

        compte = _parse_str(row[compte_idx] if compte_idx < len(row) else None, max_len=20)
        if not compte:
            continue

        raw_debit = row[debit_idx] if debit_idx is not None and debit_idx < len(row) else None
        debit = _parse_decimal(raw_debit) or Decimal("0")
        raw_credit = row[credit_idx] if credit_idx is not None and credit_idx < len(row) else None
        credit = _parse_decimal(raw_credit) or Decimal("0")

        if debit == 0 and credit == 0:
            continue

        raw_label = row[libelle_idx] if libelle_idx is not None and libelle_idx < len(row) else None
        label = _parse_str(raw_label, max_len=500) or "Import Excel"

        local_offset += 1
        entry = AccountingEntry(
            entry_number=f"{base_count + local_offset:06d}",
            date=entry_date,
            account_number=compte,
            label=label,
            debit=debit,
            credit=credit,
            source_type=EntrySourceType.MANUAL,
        )
        entries_to_add.append(entry)

    try:
        for entry in entries_to_add:
            db.add(entry)
        await db.flush()
        result.entries_created += len(entries_to_add)
        logger.info("Entries import done — created=%d", result.entries_created)
    except Exception as exc:
        logger.error("Entries flush failed: %s", exc, exc_info=True)
        result.errors.append(f"Erreur import écritures : {exc}")
        await db.rollback()


# ---------------------------------------------------------------------------
# Preview (dry-run — no DB writes)
# ---------------------------------------------------------------------------


class PreviewResult:
    """Dry-run parse summary with sample rows."""

    def __init__(self) -> None:
        self.sheets: list[dict] = []
        self.estimated_contacts: int = 0
        self.estimated_invoices: int = 0
        self.estimated_payments: int = 0
        self.estimated_entries: int = 0
        self.errors: list[str] = []
        self.sample_rows: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "sheets": self.sheets,
            "estimated_contacts": self.estimated_contacts,
            "estimated_invoices": self.estimated_invoices,
            "estimated_payments": self.estimated_payments,
            "estimated_entries": self.estimated_entries,
            "sample_rows": self.sample_rows,
            "errors": self.errors,
        }


def _preview_sheet_gestion(ws: Any, sheet_name: str, preview: PreviewResult) -> None:
    """Count parseable rows without touching the DB."""
    sheet_lower = sheet_name.lower()
    header_info = _detect_header_row(ws, ["montant", "date"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["nom", "prenom"])
    if header_info is None:
        preview.sheets.append({"name": sheet_name, "rows": 0, "skipped": True})
        return

    header_row, col_map = header_info
    count = 0
    is_contact = any(k in sheet_lower for k in ("contact", "fourniss"))
    is_payment = any(k in sheet_lower for k in ("paie", "règl", "encaiss"))

    montant_idx = next((col_map[k] for k in col_map if "montant" in k or "total" in k), None)
    nom_idx = next((col_map[k] for k in col_map if "nom" in k), None)

    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if all(c is None for c in row):
            continue
        if is_contact and nom_idx is not None:
            if _parse_str(row[nom_idx] if nom_idx < len(row) else None):
                count += 1
        elif montant_idx is not None:
            val = _parse_decimal(row[montant_idx] if montant_idx < len(row) else None)
            if val and val > 0:
                count += 1
                # Collect up to 5 sample rows
                if len(preview.sample_rows) < 5:
                    preview.sample_rows.append(
                        {
                            k: _parse_str(row[v] if v < len(row) else None)
                            for k, v in col_map.items()
                        }
                    )

    preview.sheets.append({"name": sheet_name, "rows": count})
    if is_contact:
        preview.estimated_contacts += count
    elif is_payment:
        preview.estimated_payments += count
    else:
        preview.estimated_invoices += count


def _preview_sheet_comptabilite(ws: Any, sheet_name: str, preview: PreviewResult) -> None:
    """Count parseable accounting entry rows."""
    header_info = _detect_header_row(ws, ["compte", "débit"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["compte", "credit"])
    if header_info is None:
        preview.sheets.append({"name": sheet_name, "rows": 0, "skipped": True})
        return

    header_row, col_map = header_info
    compte_idx = next((col_map[k] for k in col_map if "compte" in k), None)
    debit_idx = next((col_map[k] for k in col_map if "débit" in k or "debit" in k), None)
    credit_idx = next((col_map[k] for k in col_map if "crédit" in k or "credit" in k), None)

    count = 0
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if all(c is None for c in row):
            continue
        compte = _parse_str(
            row[compte_idx] if compte_idx is not None and compte_idx < len(row) else None
        )
        if not compte:
            continue
        d = _parse_decimal(
            row[debit_idx] if debit_idx is not None and debit_idx < len(row) else None
        ) or Decimal("0")
        c = _parse_decimal(
            row[credit_idx] if credit_idx is not None and credit_idx < len(row) else None
        ) or Decimal("0")
        if d != 0 or c != 0:
            count += 1
            if len(preview.sample_rows) < 5:
                preview.sample_rows.append(
                    {k: _parse_str(row[v] if v < len(row) else None) for k, v in col_map.items()}
                )

    preview.sheets.append({"name": sheet_name, "rows": count})
    preview.estimated_entries += count


def preview_gestion_file(file_bytes: bytes) -> PreviewResult:
    """Dry-run parse of a Gestion file — no DB writes."""
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    preview = PreviewResult()
    try:
        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        preview.errors.append(f"Impossible d'ouvrir le fichier : {exc}")
        return preview

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        _preview_sheet_gestion(ws, sheet_name, preview)

    return preview


def preview_comptabilite_file(file_bytes: bytes) -> PreviewResult:
    """Dry-run parse of a Comptabilité file — no DB writes."""
    from io import BytesIO  # noqa: PLC0415

    import openpyxl  # noqa: PLC0415

    preview = PreviewResult()
    try:
        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        preview.errors.append(f"Impossible d'ouvrir le fichier : {exc}")
        return preview

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        _preview_sheet_comptabilite(ws, sheet_name, preview)

    return preview
