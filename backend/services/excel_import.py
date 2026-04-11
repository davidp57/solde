"""Excel import service — parse and import contacts, invoices, payments from Excel files."""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_DATE_LIKE_TEXT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$|^\d{2}/\d{2}/\d{4}$|^\d{2}-\d{2}-\d{4}$"
)
_GESTION_IMPORT_ORDER = ("contacts", "invoices", "payments", "cash", "bank")

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
        self.cash_created: int = 0
        self.bank_created: int = 0
        self.skipped: int = 0
        self.errors: list[str] = []

    def to_dict(self) -> dict:
        return {
            "contacts_created": self.contacts_created,
            "invoices_created": self.invoices_created,
            "payments_created": self.payments_created,
            "entries_created": self.entries_created,
            "cash_created": self.cash_created,
            "bank_created": self.bank_created,
            "skipped": self.skipped,
            "errors": self.errors,
        }

    def reset_persisted_counts(self) -> None:
        """Reset counters when a global rollback cancels all pending writes."""
        self.contacts_created = 0
        self.invoices_created = 0
        self.payments_created = 0
        self.entries_created = 0
        self.cash_created = 0
        self.bank_created = 0
        self.skipped = 0


@dataclass(slots=True)
class ParsedSheet:
    """Normalized header-level view of a worksheet."""

    header_row: int
    col_map: dict[str, int]
    missing_columns: list[str]


@dataclass(slots=True)
class NormalizedInvoiceRow:
    """Validated invoice row ready for preview or persistence."""

    source_row_number: int
    invoice_date: date
    amount: Decimal
    contact_name: str
    invoice_number: str | None
    label: str


@dataclass(slots=True)
class NormalizedPaymentRow:
    """Validated payment row ready for preview or persistence."""

    source_row_number: int
    payment_date: date
    amount: Decimal
    method: str
    invoice_ref: str
    contact_name: str
    cheque_number: str | None
    deposited: bool
    deposit_date: date | None


@dataclass(slots=True)
class NormalizedContactRow:
    """Validated contact row ready for preview or persistence."""

    source_row_number: int
    nom: str
    prenom: str | None
    email: str | None


@dataclass(slots=True)
class NormalizedCashRow:
    """Validated cash movement row ready for preview or persistence."""

    source_row_number: int
    entry_date: date
    amount: Decimal
    movement_type: str
    description: str


@dataclass(slots=True)
class NormalizedBankRow:
    """Validated bank transaction row ready for preview or persistence."""

    source_row_number: int
    entry_date: date
    amount: Decimal
    description: str
    balance_after: Decimal


# ---------------------------------------------------------------------------
# Excel parsing helpers
# ---------------------------------------------------------------------------


def _parse_decimal(value: Any) -> Decimal | None:
    """Parse a cell value into Decimal, returning None if not valid."""
    if value is None or value == "":
        return None
    try:
        # Handle French locale: "1 234,56" → "1234.56"
        cleaned = (
            str(value).strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
        )
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


def _normalize_text(value: str) -> str:
    """Normalize text for accent-insensitive matching."""
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _find_col_idx(col_map: dict[str, int], *fragments: str) -> int | None:
    """Find the first column whose normalized label contains one fragment."""
    normalized_fragments = [_normalize_text(fragment) for fragment in fragments]
    for key, idx in col_map.items():
        normalized_key = _normalize_text(key)
        if any(fragment in normalized_key for fragment in normalized_fragments):
            return idx
    return None


def _sheet_has_content(ws: Any) -> bool:
    """Return True if the worksheet contains any non-empty cell."""
    for row in ws.iter_rows(values_only=True):
        if any(cell not in (None, "") for cell in row):
            return True
    return False


def _classify_gestion_sheet(sheet_name: str) -> tuple[str | None, str | None]:
    """Classify a gestion worksheet into a supported import kind or ignore reason."""
    key = _normalize_text(sheet_name)
    ignored_markers = (
        "aide",
        "todo",
        "depot",
        "montant total",
        "verification",
        "prevision",
        "bilan financier",
        "cdd",
        "salaire",
    )
    if any(marker in key for marker in ignored_markers):
        return None, "auxiliary-sheet"
    if any(marker in key for marker in ("fact", "client", "adh")):
        return "invoices", None
    if any(marker in key for marker in ("paie", "regl", "encaiss")):
        return "payments", None
    if any(marker in key for marker in ("contact", "fourniss")):
        return "contacts", None
    if any(marker in key for marker in ("caisse", "cash")):
        return "cash", None
    if any(marker in key for marker in ("banque", "bank", "relev")):
        return "bank", None
    return None, "unmapped-sheet"


def _classify_comptabilite_sheet(sheet_name: str) -> tuple[str | None, str | None]:
    """Classify a comptabilité worksheet into a supported import kind or ignore reason."""
    key = _normalize_text(sheet_name)
    if "saisie" in key:
        return None, "entry-helper-sheet"
    ignored_markers = (
        "donnees generales",
        "cle de repartition",
        "nomenclature",
        "grand livre",
        "balance",
        "etat factures",
        "extrait",
        "analytique",
        "bilan",
        "compte de resultat",
    )
    if any(marker in key for marker in ignored_markers):
        return None, "report-sheet"
    if key == "journal":
        return "entries", None
    if any(marker in key for marker in ("journal", "ecrit", "compta")):
        return "entries", None
    return None, "unmapped-sheet"


def _register_preview_contact(preview: PreviewResult, value: Any) -> None:
    """Register a candidate contact name discovered during preview."""
    name = _normalize_text(_parse_str(value))
    if name:
        preview._candidate_contacts.add(name)
        preview.estimated_contacts = len(preview._candidate_contacts)


def _find_invoice_number_idx(col_map: dict[str, int], *, exclude_idx: int | None) -> int | None:
    """Find the invoice number/reference column while avoiding false positives."""
    for key, idx in col_map.items():
        if exclude_idx is not None and idx == exclude_idx:
            continue
        normalized_key = _normalize_text(key)
        if any(fragment in normalized_key for fragment in ("ref facture", "reference", "facture", "numero", "num")):
            if "etat" not in normalized_key and "montant" not in normalized_key:
                return idx
    return None


def _normalize_invoice_label(value: Any) -> str:
    """Map workbook labels to invoice labels used by the domain model."""
    raw = _normalize_text(_parse_str(value))
    if raw in ("cs", "cours", "cours scolaires"):
        return "cs"
    if raw in ("a", "adhesion", "adhesion annuelle"):
        return "a"
    if raw in ("cs+a", "cours+adhesion", "cours adhesion"):
        return "cs+a"
    return "general"


def _is_truthy_yes(value: Any) -> bool:
    """Return True for French/English truthy yes values."""
    return _normalize_text(_parse_str(value)) in {"oui", "yes", "true", "1", "ok"}


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

    preview = preview_gestion_file(file_bytes)
    if preview.errors:
        result.errors.extend(preview.errors)
        return result

    try:
        from io import BytesIO  # noqa: PLC0415

        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        result.errors.append(f"Impossible d'ouvrir le fichier : {exc}")
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
            result.errors.append(f"Erreur import gestion : {exc}")
            return result

    return result


async def import_comptabilite_file(db: AsyncSession, file_bytes: bytes) -> ImportResult:
    """Import accounting entries from a 'Comptabilité YYYY.xlsx' file.

    Expected sheet columns (flexible column detection):
    date | N° pièce | compte | libellé | débit | crédit
    """
    import openpyxl  # noqa: PLC0415

    result = ImportResult()

    preview = preview_comptabilite_file(file_bytes)
    if preview.errors:
        result.errors.extend(preview.errors)
        return result

    try:
        from io import BytesIO  # noqa: PLC0415

        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        result.errors.append(f"Impossible d'ouvrir le fichier : {exc}")
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
        result.errors.append(f"Erreur import comptabilite : {exc}")
        return result

    return result


# ---------------------------------------------------------------------------
# Sheet-level parsers
# ---------------------------------------------------------------------------


def _detect_header_row(
    ws: Any, keywords: list[str]
) -> tuple[int, dict[str, int]] | None:
    """Find the header row and return (row_index, {col_name: col_index})."""
    normalized_keywords = [_normalize_text(keyword) for keyword in keywords]
    for row_idx, row in enumerate(ws.iter_rows(max_row=20, values_only=True), start=1):
        row_lower = [_normalize_text(_parse_str(c)) for c in row]
        matched = sum(
            1 for keyword in normalized_keywords if any(keyword in cell for cell in row_lower)
        )
        if matched >= 2:
            col_map: dict[str, int] = {}
            for col_idx, cell in enumerate(row_lower):
                col_map[cell] = col_idx
            return row_idx, col_map
    return None


def _get_row_value(row: tuple[Any, ...], idx: int | None) -> Any:
    """Safely read a row value by column index."""
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _parse_invoice_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedInvoiceRow]]:
    """Parse invoice rows into a shared normalized structure."""
    header_info = _detect_header_row(ws, ["montant", "date"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["montant", "client"])
    if header_info is None:
        return None, []

    header_row, col_map = header_info
    date_idx = _find_col_idx(col_map, "date")
    montant_idx = _find_col_idx(col_map, "montant", "total")
    nom_idx = _find_col_idx(col_map, "nom", "client", "adhérent", "adherent")
    numero_idx = _find_invoice_number_idx(col_map, exclude_idx=date_idx)
    label_idx = _find_col_idx(col_map, "motif", "libellé", "libelle", "type")

    missing_columns: list[str] = []
    if montant_idx is None:
        missing_columns.append("montant")
    if nom_idx is None:
        missing_columns.append("client")

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, []

    rows: list[NormalizedInvoiceRow] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        amount = _parse_decimal(_get_row_value(row, montant_idx))
        contact_name = _parse_str(_get_row_value(row, nom_idx))
        if amount is None or amount <= 0 or not contact_name:
            continue

        invoice_date = _parse_date(_get_row_value(row, date_idx)) or date.today()
        raw_number = _get_row_value(row, numero_idx)
        invoice_number: str | None = None
        if not isinstance(raw_number, (date, datetime)):
            candidate = _parse_str(raw_number)
            if candidate and not _DATE_LIKE_TEXT_RE.match(candidate):
                invoice_number = candidate

        rows.append(
            NormalizedInvoiceRow(
                source_row_number=source_row_number,
                invoice_date=invoice_date,
                amount=amount,
                contact_name=contact_name,
                invoice_number=invoice_number,
                label=_normalize_invoice_label(_get_row_value(row, label_idx)),
            )
        )

    return parsed_sheet, rows


def _parse_payment_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedPaymentRow]]:
    """Parse payment rows into a shared normalized structure."""
    header_info = _detect_header_row(ws, ["montant", "date"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["montant", "facture"])
    if header_info is None:
        return None, []

    header_row, col_map = header_info
    date_idx = _find_col_idx(col_map, "date paiement", "date")
    montant_idx = _find_col_idx(col_map, "montant")
    mode_idx = _find_col_idx(
        col_map,
        "mode",
        "règl",
        "regl",
        "réf paiement",
        "ref paiement",
    )
    invoice_idx = _find_invoice_number_idx(col_map, exclude_idx=date_idx)
    nom_idx = _find_col_idx(col_map, "nom", "client", "adhérent", "adherent")
    cheque_idx = _find_col_idx(
        col_map,
        "numéro du chèque",
        "numero du cheque",
        "chèque",
        "cheque",
    )
    deposited_idx = _find_col_idx(col_map, "encaissé", "encaisse")
    deposit_date_idx = _find_col_idx(col_map, "date encaissement")

    missing_columns: list[str] = []
    if montant_idx is None:
        missing_columns.append("montant")
    if invoice_idx is None and nom_idx is None:
        missing_columns.append("référence facture ou contact")

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, []

    rows: list[NormalizedPaymentRow] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        amount = _parse_decimal(_get_row_value(row, montant_idx))
        if amount is None or amount <= 0:
            continue

        invoice_ref = _parse_str(_get_row_value(row, invoice_idx))
        contact_name = _parse_str(_get_row_value(row, nom_idx))
        if not invoice_ref and not contact_name:
            continue

        rows.append(
            NormalizedPaymentRow(
                source_row_number=source_row_number,
                payment_date=_parse_date(_get_row_value(row, date_idx)) or date.today(),
                amount=amount,
                method=_normalize_payment_method(_get_row_value(row, mode_idx)),
                invoice_ref=invoice_ref,
                contact_name=contact_name,
                cheque_number=_parse_str(_get_row_value(row, cheque_idx)) or None,
                deposited=_is_truthy_yes(_get_row_value(row, deposited_idx)),
                deposit_date=_parse_date(_get_row_value(row, deposit_date_idx)),
            )
        )

    return parsed_sheet, rows


def _parse_contact_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedContactRow]]:
    """Parse contact rows into a shared normalized structure."""
    header_info = _detect_header_row(ws, ["nom", "prenom"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["nom", "email"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["nom", "mail"])
    if header_info is None:
        return None, []

    header_row, col_map = header_info
    nom_idx = _find_col_idx(col_map, "nom")
    prenom_idx = _find_col_idx(col_map, "prenom", "prénom")
    email_idx = _find_col_idx(col_map, "email", "mail")

    missing_columns: list[str] = []
    if nom_idx is None:
        missing_columns.append("nom")

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, []

    rows: list[NormalizedContactRow] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        nom = _parse_str(_get_row_value(row, nom_idx))
        if not nom:
            continue

        prenom = _parse_str(_get_row_value(row, prenom_idx)) or None
        email = _parse_str(_get_row_value(row, email_idx)) or None
        rows.append(
            NormalizedContactRow(
                source_row_number=source_row_number,
                nom=nom,
                prenom=prenom,
                email=email,
            )
        )

    return parsed_sheet, rows


def _parse_cash_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedCashRow]]:
    """Parse cash rows into a shared normalized structure."""
    header_info = _detect_header_row(ws, ["date", "entree"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["date", "sortie"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["date", "montant"])
    if header_info is None:
        return None, []

    header_row, col_map = header_info
    date_idx = _find_col_idx(col_map, "date")
    entree_idx = _find_col_idx(col_map, "entree", "entrée", "recette", "credit", "crédit")
    sortie_idx = _find_col_idx(col_map, "sortie", "depense", "dépense", "debit", "débit")
    montant_idx = (
        _find_col_idx(col_map, "montant", "total")
        if entree_idx is None and sortie_idx is None
        else None
    )
    type_idx = (
        _find_col_idx(col_map, "type", "sens") if montant_idx is not None else None
    )
    libelle_idx = _find_col_idx(col_map, "libel", "descr", "label", "objet")

    missing_columns: list[str] = []
    if date_idx is None:
        missing_columns.append("date")
    if entree_idx is None and sortie_idx is None and montant_idx is None:
        missing_columns.append("entrée/sortie ou montant")

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, []

    rows: list[NormalizedCashRow] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        entry_date = _parse_date(_get_row_value(row, date_idx))
        if entry_date is None:
            continue

        amount: Decimal | None = None
        movement_type: str | None = None
        if entree_idx is not None or sortie_idx is not None:
            entree = _parse_decimal(_get_row_value(row, entree_idx))
            sortie = _parse_decimal(_get_row_value(row, sortie_idx))
            if entree is not None and entree > 0:
                amount = entree
                movement_type = "in"
            elif sortie is not None and sortie > 0:
                amount = sortie
                movement_type = "out"
        elif montant_idx is not None:
            amount = _parse_decimal(_get_row_value(row, montant_idx))
            raw_type = _normalize_text(_parse_str(_get_row_value(row, type_idx)))
            if raw_type in ("e", "in", "entree", "recette", "credit"):
                movement_type = "in"
            else:
                movement_type = "out"

        if amount is None or amount <= 0 or movement_type is None:
            continue

        rows.append(
            NormalizedCashRow(
                source_row_number=source_row_number,
                entry_date=entry_date,
                amount=amount,
                movement_type=movement_type,
                description=_parse_str(_get_row_value(row, libelle_idx), max_len=500)
                or "Import Excel",
            )
        )

    return parsed_sheet, rows


def _parse_bank_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedBankRow]]:
    """Parse bank rows into a shared normalized structure."""
    header_info = _detect_header_row(ws, ["date", "debit"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["date", "credit"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["date", "montant"])
    if header_info is None:
        return None, []

    header_row, col_map = header_info
    date_idx = _find_col_idx(col_map, "date")
    debit_idx = _find_col_idx(col_map, "débit", "debit")
    credit_idx = _find_col_idx(col_map, "crédit", "credit")
    montant_idx = (
        _find_col_idx(col_map, "montant")
        if debit_idx is None and credit_idx is None
        else None
    )
    libelle_idx = _find_col_idx(col_map, "libel", "descr", "label", "intitul")
    solde_idx = _find_col_idx(col_map, "solde", "balance")

    missing_columns: list[str] = []
    if date_idx is None:
        missing_columns.append("date")
    if debit_idx is None and credit_idx is None and montant_idx is None:
        missing_columns.append("débit/crédit ou montant")

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, []

    rows: list[NormalizedBankRow] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        entry_date = _parse_date(_get_row_value(row, date_idx))
        if entry_date is None:
            continue

        amount: Decimal | None = None
        if debit_idx is not None or credit_idx is not None:
            debit = _parse_decimal(_get_row_value(row, debit_idx)) or Decimal("0")
            credit = _parse_decimal(_get_row_value(row, credit_idx)) or Decimal("0")
            if credit > 0:
                amount = credit
            elif debit > 0:
                amount = -debit
        elif montant_idx is not None:
            amount = _parse_decimal(_get_row_value(row, montant_idx))

        if amount is None or amount == 0:
            continue

        rows.append(
            NormalizedBankRow(
                source_row_number=source_row_number,
                entry_date=entry_date,
                amount=amount,
                description=_parse_str(_get_row_value(row, libelle_idx), max_len=500)
                or "Import Excel",
                balance_after=_parse_decimal(_get_row_value(row, solde_idx))
                or Decimal("0"),
            )
        )

    return parsed_sheet, rows


async def _import_contacts_sheet(
    db: AsyncSession, ws: Any, result: ImportResult
) -> None:
    """Import contacts from a sheet."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact, ContactType  # noqa: PLC0415

    parsed_sheet, normalized_rows = _parse_contact_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    for contact_row in normalized_rows:
        # Idempotency: skip if contact with same nom+prenom exists
        existing = await db.execute(
            select(Contact).where(
                Contact.nom == contact_row.nom,
                Contact.prenom == contact_row.prenom,
            )
        )
        if existing.scalars().first() is not None:
            result.skipped += 1
            continue

        contact = Contact(
            nom=contact_row.nom,
            prenom=contact_row.prenom,
            email=contact_row.email,
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


async def _import_invoices_sheet(
    db: AsyncSession, ws: Any, result: ImportResult
) -> None:
    """Import invoices from a sheet with flexible column detection."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact, ContactType  # noqa: PLC0415
    from backend.models.invoice import (  # noqa: PLC0415
        Invoice,
        InvoiceLabel,
        InvoiceStatus,
        InvoiceType,
    )

    parsed_sheet, normalized_rows = _parse_invoice_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        result.skipped += 1
        return

    logger.info(
        "Importing invoices sheet — rows=%s missing_columns=%s",
        len(normalized_rows),
        parsed_sheet.missing_columns,
    )

    seen_numbers: set[str] = set()  # deduplicate within the current batch
    created_invoices: list[Invoice] = []
    generated_number_index = 0
    for invoice_row in normalized_rows:
        invoice_date = invoice_row.invoice_date
        total = invoice_row.amount

        # Find or create contact
        contact_id: int | None = None
        existing = await db.execute(
            select(Contact).where(Contact.nom.ilike(f"%{invoice_row.contact_name}%"))
        )
        contact = existing.scalars().first()
        if contact:
            contact_id = contact.id
        else:
            new_contact = Contact(nom=invoice_row.contact_name, type=ContactType.CLIENT)
            db.add(new_contact)
            await db.flush()
            contact_id = new_contact.id
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

        # Deduplicate within the current batch (avoid UNIQUE constraint in same flush)
        if number_raw in seen_numbers:
            logger.debug(
                "Row %d — duplicate number '%s' in batch, skipping",
                invoice_row.source_row_number,
                number_raw,
            )
            result.skipped += 1
            continue

        # Idempotency: skip if already in DB
        existing_inv = await db.execute(
            select(Invoice).where(Invoice.number == number_raw)
        )
        if existing_inv.scalar_one_or_none() is not None:
            logger.debug(
                "Row %d — invoice '%s' already exists, skipping",
                invoice_row.source_row_number,
                number_raw,
            )
            result.skipped += 1
            continue

        seen_numbers.add(number_raw)

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

    try:
        await db.flush()
        # Generate accounting entries for each new invoice (no-op if no rules configured)
        from backend.services.accounting_engine import (
            generate_entries_for_invoice,
        )  # noqa: PLC0415

        for inv_obj in created_invoices:
            try:
                entries = await generate_entries_for_invoice(db, inv_obj)
                result.entries_created += len(entries)
            except Exception as e:
                logger.warning(
                    "Accounting entries skipped for invoice '%s': %s", inv_obj.number, e
                )
        logger.info(
            "Invoices import done — created=%d skipped=%d entries=%d",
            result.invoices_created,
            result.skipped,
            result.entries_created,
        )
    except Exception as exc:
        logger.error("Invoices flush failed: %s", exc, exc_info=True)
        result.errors.append(f"Erreur import factures : {exc}")
        await db.rollback()


async def _import_payments_sheet(
    db: AsyncSession, ws: Any, result: ImportResult
) -> None:
    """Import payments from a sheet."""
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.contact import Contact  # noqa: PLC0415
    from backend.models.invoice import Invoice, InvoiceType  # noqa: PLC0415
    from backend.models.payment import Payment  # noqa: PLC0415

    parsed_sheet, normalized_rows = _parse_payment_sheet(ws)
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

        # Try to find matching invoice
        invoice_ref = payment_row.invoice_ref
        invoice_id: int | None = None
        contact_id: int | None = None
        inv_type: InvoiceType = InvoiceType.CLIENT

        if invoice_ref:
            inv_result = await db.execute(
                select(Invoice).where(Invoice.number.ilike(f"%{invoice_ref}%"))
            )
            inv = inv_result.scalars().first()
            if inv:
                invoice_id = inv.id
                contact_id = inv.contact_id
                inv_type = inv.type

        # Fallback: find contact by name and pick their latest invoice
        if invoice_id is None and payment_row.contact_name:
            c_result = await db.execute(
                select(Contact).where(Contact.nom.ilike(f"%{payment_row.contact_name}%"))
            )
            c = c_result.scalars().first()
            if c:
                contact_id = c.id
                inv_result2 = await db.execute(
                    select(Invoice)
                    .where(Invoice.contact_id == c.id)
                    .order_by(Invoice.date.desc())
                    .limit(1)
                )
                inv2 = inv_result2.scalars().first()
                if inv2:
                    invoice_id = inv2.id
                    inv_type = inv2.type

        if invoice_id is None or contact_id is None:
            logger.debug(
                "Row %d — payment skipped: no matching invoice/contact ref='%s'",
                payment_row.source_row_number,
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

    try:
        await db.flush()
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
        await db.flush()
        logger.info(
            "Payments import done — created=%d skipped=%d entries=%d",
            result.payments_created,
            result.skipped,
            result.entries_created,
        )
    except Exception as exc:
        logger.error("Payments flush failed: %s", exc, exc_info=True)
        result.errors.append(f"Erreur import paiements : {exc}")
        await db.rollback()


async def _import_cash_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import cash register movements from a 'Caisse' sheet.

    Expected columns (flexible): date | libellé/description | entrée | sortie
    or: date | description | montant | type (E/S or in/out)
    """
    from backend.models.cash import CashMovementType, CashRegister  # noqa: PLC0415

    parsed_sheet, normalized_rows = _parse_cash_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        logger.info(
            "Cash sheet skipped — header not detected or missing columns=%s",
            parsed_sheet.missing_columns if parsed_sheet else None,
        )
        return

    for cash_row in normalized_rows:
        entry = CashRegister(
            date=cash_row.entry_date,
            amount=cash_row.amount,
            type=CashMovementType(cash_row.movement_type),
            description=cash_row.description,
            balance_after=Decimal("0"),
        )
        db.add(entry)
        result.cash_created += 1

    try:
        await db.flush()
        logger.info("Cash import done — created=%d", result.cash_created)
    except Exception as exc:
        logger.error("Cash flush failed: %s", exc, exc_info=True)
        result.errors.append(f"Erreur import caisse : {exc}")
        await db.rollback()


async def _import_bank_sheet(db: AsyncSession, ws: Any, result: ImportResult) -> None:
    """Import bank transactions from a 'Banque' or 'Relevé' sheet.

    Expected columns (flexible): date | libellé | débit | crédit | solde
    or: date | description | montant (positive=credit, negative=debit)
    """
    from backend.models.bank import (
        BankTransaction,
        BankTransactionSource,
    )  # noqa: PLC0415

    parsed_sheet, normalized_rows = _parse_bank_sheet(ws)
    if parsed_sheet is None or parsed_sheet.missing_columns:
        logger.info(
            "Bank sheet skipped — header not detected or missing columns=%s",
            parsed_sheet.missing_columns if parsed_sheet else None,
        )
        return

    for bank_row in normalized_rows:
        entry = BankTransaction(
            date=bank_row.entry_date,
            amount=bank_row.amount,
            description=bank_row.description,
            balance_after=bank_row.balance_after,
            source=BankTransactionSource.IMPORT,
        )
        db.add(entry)
        result.bank_created += 1

    try:
        await db.flush()
        logger.info("Bank import done — created=%d", result.bank_created)
    except Exception as exc:
        logger.error("Bank flush failed: %s", exc, exc_info=True)
        result.errors.append(f"Erreur import banque : {exc}")
        await db.rollback()


async def _import_entries_sheet(
    db: AsyncSession, ws: Any, result: ImportResult
) -> None:
    """Import accounting entries from a comptabilité sheet."""
    from sqlalchemy import func, select  # noqa: PLC0415

    from backend.models.accounting_entry import (
        AccountingEntry,
        EntrySourceType,
    )  # noqa: PLC0415

    header_info = _detect_header_row(ws, ["compte", "débit"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["compte", "credit"])
    if header_info is None:
        result.skipped += 1
        return

    header_row, col_map = header_info

    date_idx = next((col_map[k] for k in col_map if "date" in k), None)
    compte_idx = next((col_map[k] for k in col_map if "compte" in k), None)
    libelle_idx = next(
        (col_map[k] for k in col_map if "libel" in k or "label" in k), None
    )
    debit_idx = next(
        (col_map[k] for k in col_map if "débit" in k or "debit" in k), None
    )
    credit_idx = next(
        (col_map[k] for k in col_map if "crédit" in k or "credit" in k), None
    )

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
            _parse_date(row[date_idx])
            if date_idx is not None and date_idx < len(row)
            else None
        )
        if entry_date is None:
            entry_date = date.today()

        compte = _parse_str(
            row[compte_idx] if compte_idx < len(row) else None, max_len=20
        )
        if not compte:
            continue

        raw_debit = (
            row[debit_idx] if debit_idx is not None and debit_idx < len(row) else None
        )
        debit = _parse_decimal(raw_debit) or Decimal("0")
        raw_credit = (
            row[credit_idx]
            if credit_idx is not None and credit_idx < len(row)
            else None
        )
        credit = _parse_decimal(raw_credit) or Decimal("0")

        if debit == 0 and credit == 0:
            continue

        raw_label = (
            row[libelle_idx]
            if libelle_idx is not None and libelle_idx < len(row)
            else None
        )
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
    """Dry-run parse summary with detailed sheet diagnostics."""

    def __init__(self) -> None:
        self.sheets: list[dict[str, Any]] = []
        self.estimated_contacts: int = 0
        self.estimated_invoices: int = 0
        self.estimated_payments: int = 0
        self.estimated_entries: int = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.sample_rows: list[dict[str, Any]] = []
        self.can_import: bool = False
        self._candidate_contacts: set[str] = set()

    def to_dict(self) -> dict:
        return {
            "sheets": self.sheets,
            "estimated_contacts": self.estimated_contacts,
            "estimated_invoices": self.estimated_invoices,
            "estimated_payments": self.estimated_payments,
            "estimated_entries": self.estimated_entries,
            "sample_rows": self.sample_rows,
            "errors": self.errors,
            "warnings": self.warnings,
            "can_import": self.can_import,
        }


def _make_sheet_preview(
    *,
    sheet_name: str,
    kind: str,
    status: str,
    header_row: int | None = None,
    rows: int = 0,
    detected_columns: list[str] | None = None,
    missing_columns: list[str] | None = None,
    sample_rows: list[dict[str, str]] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": sheet_name,
        "kind": kind,
        "status": status,
        "header_row": header_row,
        "rows": rows,
        "detected_columns": detected_columns or [],
        "missing_columns": missing_columns or [],
        "sample_rows": sample_rows or [],
        "warnings": warnings or [],
        "errors": errors or [],
    }


def _append_sheet_preview(preview: PreviewResult, sheet: dict[str, Any]) -> None:
    preview.sheets.append(sheet)
    preview.errors.extend(f"{sheet['name']} — {error}" for error in sheet["errors"])
    preview.warnings.extend(
        f"{sheet['name']} — {warning}" for warning in sheet["warnings"]
    )
    if sheet["status"] == "recognized" and sheet["rows"] > 0:
        preview.can_import = True
        for row in sheet["sample_rows"]:
            if len(preview.sample_rows) >= 5:
                break
            preview.sample_rows.append({"sheet": sheet["name"], **row})


def _collect_sample_rows(
    ws: Any, header_row: int, col_map: dict[str, int], *, limit: int = 3
) -> list[dict[str, str]]:
    samples: list[dict[str, str]] = []
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if all(cell is None for cell in row):
            continue
        samples.append(
            {
                key: _parse_str(row[idx] if idx < len(row) else None)
                for key, idx in col_map.items()
            }
        )
        if len(samples) >= limit:
            break
    return samples


def _preview_sheet_gestion(ws: Any, sheet_name: str, preview: PreviewResult) -> None:
    """Count parseable rows and report diagnostics for gestion files."""
    kind, reason = _classify_gestion_sheet(sheet_name)
    if kind is None:
        status = "ignored" if _sheet_has_content(ws) else "empty"
        warnings = []
        if status == "ignored":
            if reason == "auxiliary-sheet":
                warnings.append("Feuille auxiliaire ignoree par la preview")
            elif reason == "unmapped-sheet":
                warnings.append("Feuille non reconnue et ignoree")
        _append_sheet_preview(
            preview,
            _make_sheet_preview(
                sheet_name=sheet_name,
                kind="ignored",
                status=status,
                warnings=warnings,
            ),
        )
        return

    if kind == "contacts":
        header_info = _detect_header_row(ws, ["nom", "prenom"]) or _detect_header_row(
            ws, ["nom", "email"]
        )
    elif kind == "payments":
        header_info = _detect_header_row(ws, ["montant", "date"]) or _detect_header_row(
            ws, ["montant", "facture"]
        )
    elif kind == "bank":
        header_info = _detect_header_row(ws, ["date", "montant"]) or _detect_header_row(
            ws, ["date", "debit"]
        )
    elif kind == "cash":
        header_info = _detect_header_row(ws, ["date", "entree"]) or _detect_header_row(
            ws, ["date", "montant"]
        )
    else:
        header_info = _detect_header_row(ws, ["montant", "date"]) or _detect_header_row(
            ws, ["montant", "client"]
        )

    if header_info is None:
        _append_sheet_preview(
            preview,
            _make_sheet_preview(
                sheet_name=sheet_name,
                kind=kind,
                status="ignored",
                warnings=["Structure non reconnue, feuille ignoree par la preview"],
            ),
        )
        return

    header_row, col_map = header_info
    detected_columns = list(col_map.keys())
    count = 0
    missing_columns: list[str] = []

    if kind == "contacts":
        parsed_sheet, contact_rows = _parse_contact_sheet(ws)
        if parsed_sheet is None:
            _append_sheet_preview(
                preview,
                _make_sheet_preview(
                    sheet_name=sheet_name,
                    kind=kind,
                    status="ignored",
                    warnings=["Structure non reconnue, feuille ignoree par la preview"],
                ),
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(contact_rows)
        if not missing_columns:
            for contact_row in contact_rows:
                _register_preview_contact(
                    preview,
                    f"{contact_row.nom} {contact_row.prenom or ''}".strip(),
                )
    elif kind == "invoices":
        parsed_sheet, invoice_rows = _parse_invoice_sheet(ws)
        if parsed_sheet is None:
            _append_sheet_preview(
                preview,
                _make_sheet_preview(
                    sheet_name=sheet_name,
                    kind=kind,
                    status="ignored",
                    warnings=["Structure non reconnue, feuille ignoree par la preview"],
                ),
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(invoice_rows)
        if not missing_columns:
            for invoice_row in invoice_rows:
                _register_preview_contact(preview, invoice_row.contact_name)
            preview.estimated_invoices += count
    elif kind == "payments":
        parsed_sheet, payment_rows = _parse_payment_sheet(ws)
        if parsed_sheet is None:
            _append_sheet_preview(
                preview,
                _make_sheet_preview(
                    sheet_name=sheet_name,
                    kind=kind,
                    status="ignored",
                    warnings=["Structure non reconnue, feuille ignoree par la preview"],
                ),
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(payment_rows)
        if not missing_columns:
            for payment_row in payment_rows:
                if payment_row.contact_name:
                    _register_preview_contact(preview, payment_row.contact_name)
            preview.estimated_payments += count
    elif kind == "bank":
        parsed_sheet, bank_rows = _parse_bank_sheet(ws)
        if parsed_sheet is None:
            _append_sheet_preview(
                preview,
                _make_sheet_preview(
                    sheet_name=sheet_name,
                    kind=kind,
                    status="ignored",
                    warnings=["Structure non reconnue, feuille ignoree par la preview"],
                ),
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(bank_rows)
    elif kind == "cash":
        parsed_sheet, cash_rows = _parse_cash_sheet(ws)
        if parsed_sheet is None:
            _append_sheet_preview(
                preview,
                _make_sheet_preview(
                    sheet_name=sheet_name,
                    kind=kind,
                    status="ignored",
                    warnings=["Structure non reconnue, feuille ignoree par la preview"],
                ),
            )
            return
        header_row = parsed_sheet.header_row
        detected_columns = list(parsed_sheet.col_map.keys())
        missing_columns = parsed_sheet.missing_columns
        count = len(cash_rows)

    errors = []
    status = "recognized"
    if missing_columns:
        status = "unsupported"
        errors.append(
            f"Colonnes requises manquantes: {', '.join(missing_columns)}"
        )

    _append_sheet_preview(
        preview,
        _make_sheet_preview(
            sheet_name=sheet_name,
            kind=kind,
            status=status,
            header_row=header_row,
            rows=count,
            detected_columns=detected_columns,
            missing_columns=missing_columns,
            sample_rows=_collect_sample_rows(ws, header_row, col_map),
            errors=errors,
        ),
    )


def _preview_sheet_comptabilite(
    ws: Any, sheet_name: str, preview: PreviewResult
) -> None:
    """Count parseable accounting entry rows and report diagnostics."""
    kind, reason = _classify_comptabilite_sheet(sheet_name)
    if kind is None:
        status = "ignored" if _sheet_has_content(ws) else "empty"
        warnings = []
        if status == "ignored":
            if reason == "report-sheet":
                warnings.append("Feuille de reporting ignoree par la preview")
            elif reason == "entry-helper-sheet":
                warnings.append("Feuille d'aide a la saisie ignoree par la preview")
            elif reason == "unmapped-sheet":
                warnings.append("Feuille non reconnue et ignoree")
        _append_sheet_preview(
            preview,
            _make_sheet_preview(
                sheet_name=sheet_name,
                kind="ignored",
                status=status,
                warnings=warnings,
            ),
        )
        return

    header_info = _detect_header_row(ws, ["compte", "débit"])
    if header_info is None:
        header_info = _detect_header_row(ws, ["compte", "credit"])
    if header_info is None:
        _append_sheet_preview(
            preview,
            _make_sheet_preview(
                sheet_name=sheet_name,
                kind=kind,
                status="ignored",
                warnings=["Structure de journal non reconnue, feuille ignoree par la preview"],
            ),
        )
        return

    header_row, col_map = header_info
    detected_columns = list(col_map.keys())
    compte_idx = _find_col_idx(col_map, "compte")
    debit_idx = _find_col_idx(col_map, "débit", "debit")
    credit_idx = _find_col_idx(col_map, "crédit", "credit")

    missing_columns: list[str] = []
    if compte_idx is None:
        missing_columns.append("compte")
    if debit_idx is None and credit_idx is None:
        missing_columns.append("débit/crédit")

    count = 0
    if not missing_columns:
        for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
            if all(cell is None for cell in row):
                continue
            compte = _parse_str(
                row[compte_idx] if compte_idx is not None and compte_idx < len(row) else None
            )
            debit = _parse_decimal(
                row[debit_idx] if debit_idx is not None and debit_idx < len(row) else None
            ) or Decimal("0")
            credit = _parse_decimal(
                row[credit_idx] if credit_idx is not None and credit_idx < len(row) else None
            ) or Decimal("0")
            if compte and (debit != 0 or credit != 0):
                count += 1
        preview.estimated_entries += count

    errors = []
    status = "recognized"
    if missing_columns:
        status = "unsupported"
        errors.append(
            f"Colonnes requises manquantes: {', '.join(missing_columns)}"
        )

    _append_sheet_preview(
        preview,
        _make_sheet_preview(
            sheet_name=sheet_name,
            kind=kind,
            status=status,
            header_row=header_row,
            rows=count,
            detected_columns=detected_columns,
            missing_columns=missing_columns,
            sample_rows=_collect_sample_rows(ws, header_row, col_map),
            errors=errors,
        ),
    )


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

    preview.can_import = preview.can_import and not preview.errors

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

    preview.can_import = preview.can_import and not preview.errors

    return preview
