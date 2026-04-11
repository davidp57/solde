"""Business policy helpers for historical Excel import classification."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any, TypeVar

from backend.services.excel_import_types import (
    NormalizedContactRow,
    NormalizedInvoiceRow,
    RowIgnoredIssue,
    RowValidationIssue,
)

BANK_BALANCE_DESCRIPTION_MESSAGE = "ligne descriptive de solde ignoree"
ALREADY_IMPORTED_MESSAGE_PREFIX = "Fichier deja importe"
BANK_INVALID_AMOUNT_MESSAGE = "montant manquant ou nul"
BANK_INVALID_DATE_MESSAGE = "date manquante ou invalide"
BANK_REQUIRED_DATE_OR_AMOUNT_COLUMNS = ("date", "débit/crédit ou montant")
CASH_INITIAL_BALANCE_MESSAGE = "ligne de solde initial ignoree"
CASH_PENDING_DEPOSIT_MESSAGE = "prevision de remise d'especes sans date, ligne ignoree"
CASH_INVALID_DATE_MESSAGE = "date manquante ou invalide"
CASH_INVALID_MOVEMENT_MESSAGE = "mouvement ou montant manquant/invalide"
CASH_REQUIRED_DATE_OR_AMOUNT_COLUMNS = ("date", "entrée/sortie ou montant")
CONTACT_REQUIRED_NAME_MESSAGE = "nom"
COMPTABILITE_ENTRY_HELPER_SHEET_MESSAGE = "Feuille d'aide a la saisie ignoree par la preview"
COMPTABILITE_COEXISTENCE_BLOCKED_MESSAGE_PREFIX = (
    "Import comptabilite bloque : des ecritures auto-generees "
    "issues de la gestion existent deja en base"
)
COMPTABILITE_REPORT_SHEET_MESSAGE = "Feuille de reporting ignoree par la preview"
COMPTABILITE_UNKNOWN_STRUCTURE_MESSAGE = (
    "Structure de journal non reconnue, feuille ignoree par la preview"
)
DUPLICATE_CONTACT_MESSAGE = "contact duplique dans le fichier, ligne ignoree"
DUPLICATE_INVOICE_MESSAGE = "facture dupliquee dans le fichier, ligne ignoree"
ENTRY_INVALID_CREDIT_MESSAGE = "montant credit invalide"
ENTRY_INVALID_DATE_MESSAGE = "date invalide"
ENTRY_INVALID_DEBIT_MESSAGE = "montant debit invalide"
ENTRY_MISSING_ACCOUNT_MESSAGE = "compte manquant"
ENTRY_REQUIRED_ACCOUNT_OR_AMOUNT_COLUMNS = ("compte", "débit/crédit")
EXISTING_CONTACT_MESSAGE = "contact deja existant, ligne ignoree"
EXISTING_INVOICE_MESSAGE = "facture deja existante, ligne ignoree"
GESTION_AUXILIARY_SHEET_MESSAGE = "Feuille auxiliaire ignoree par la preview"
GESTION_UNKNOWN_STRUCTURE_MESSAGE = "Structure non reconnue, feuille ignoree par la preview"
INVOICE_AMBIGUOUS_CONTACT_MESSAGE = "client ambigu : plusieurs contacts correspondent"
INVOICE_INVALID_AMOUNT_MESSAGE = "montant manquant ou invalide"
INVOICE_INVALID_DATE_MESSAGE = "date manquante ou invalide"
INVOICE_REQUIRED_COLUMNS = ("date", "montant", "client")
INVOICE_REQUIRED_CONTACT_MESSAGE = "client manquant"
INVOICE_TOTAL_MESSAGE = "ligne de total ignoree"
MISSING_REQUIRED_COLUMNS_MESSAGE_PREFIX = "Colonnes requises manquantes"
PAYMENT_AMBIGUOUS_CONTACT_MESSAGE = (
    "rapprochement ambigu via le contact : plusieurs factures correspondent"
)
PAYMENT_AMBIGUOUS_REFERENCE_MESSAGE = "reference facture ambigue : plusieurs factures correspondent"
PAYMENT_INVALID_AMOUNT_MESSAGE = "montant manquant ou invalide"
PAYMENT_MATCH_INVALID_MESSAGE = "paiement rapproche sans identifiant exploitable"
PAYMENT_MISSING_MATCH_MESSAGE = (
    "paiement impossible a rapprocher a une facture existante ou importee"
)
PAYMENT_UNMATCHABLE_MESSAGE = "paiement non rapprochable"
PAYMENT_REQUIRED_COLUMNS = ("montant", "référence facture ou contact")
PAYMENT_REQUIRED_REFERENCE_OR_CONTACT_MESSAGE = "reference facture ou contact manquant"
IMPORT_ERROR_MESSAGE_PREFIX = "Erreur import "
UNMAPPED_SHEET_MESSAGE = "Feuille non reconnue et ignoree"
ZERO_JOURNAL_ENTRY_MESSAGE = "ecriture a debit/credit nuls ignoree"

RowType = TypeVar("RowType")

_UNAMBIGUOUS_ISSUE_CATEGORY_BY_MESSAGE = {
    BANK_BALANCE_DESCRIPTION_MESSAGE: "bank-balance-description",
    CASH_INITIAL_BALANCE_MESSAGE: "cash-initial-balance",
    CASH_PENDING_DEPOSIT_MESSAGE: "cash-pending-deposit",
    COMPTABILITE_ENTRY_HELPER_SHEET_MESSAGE: "comptabilite-entry-helper-sheet",
    COMPTABILITE_REPORT_SHEET_MESSAGE: "comptabilite-report-sheet",
    COMPTABILITE_UNKNOWN_STRUCTURE_MESSAGE: "comptabilite-unknown-structure",
    DUPLICATE_CONTACT_MESSAGE: "duplicate-contact",
    DUPLICATE_INVOICE_MESSAGE: "duplicate-invoice",
    EXISTING_CONTACT_MESSAGE: "existing-contact",
    EXISTING_INVOICE_MESSAGE: "existing-invoice",
    GESTION_AUXILIARY_SHEET_MESSAGE: "gestion-auxiliary-sheet",
    GESTION_UNKNOWN_STRUCTURE_MESSAGE: "gestion-unknown-structure",
    INVOICE_AMBIGUOUS_CONTACT_MESSAGE: "invoice-ambiguous-contact",
    INVOICE_TOTAL_MESSAGE: "invoice-total",
    PAYMENT_AMBIGUOUS_CONTACT_MESSAGE: "payment-ambiguous-contact",
    PAYMENT_AMBIGUOUS_REFERENCE_MESSAGE: "payment-ambiguous-reference",
    PAYMENT_MATCH_INVALID_MESSAGE: "payment-invalid-match",
    PAYMENT_MISSING_MATCH_MESSAGE: "payment-unmatched",
    PAYMENT_UNMATCHABLE_MESSAGE: "payment-unmatched",
    UNMAPPED_SHEET_MESSAGE: "unmapped-sheet",
    ZERO_JOURNAL_ENTRY_MESSAGE: "zero-journal-entry",
}

_ISSUE_CATEGORY_BY_KIND_AND_MESSAGE = {
    "bank": {
        BANK_INVALID_AMOUNT_MESSAGE: "bank-invalid-amount",
        BANK_INVALID_DATE_MESSAGE: "bank-invalid-date",
    },
    "cash": {
        CASH_INVALID_DATE_MESSAGE: "cash-invalid-date",
        CASH_INVALID_MOVEMENT_MESSAGE: "cash-invalid-movement",
    },
    "contacts": {
        f"{CONTACT_REQUIRED_NAME_MESSAGE} manquant": "contact-missing-name",
    },
    "entries": {
        ENTRY_INVALID_CREDIT_MESSAGE: "entry-invalid-credit",
        ENTRY_INVALID_DATE_MESSAGE: "entry-invalid-date",
        ENTRY_INVALID_DEBIT_MESSAGE: "entry-invalid-debit",
        ENTRY_MISSING_ACCOUNT_MESSAGE: "entry-missing-account",
    },
    "invoices": {
        INVOICE_AMBIGUOUS_CONTACT_MESSAGE: "invoice-ambiguous-contact",
        INVOICE_INVALID_AMOUNT_MESSAGE: "invoice-invalid-amount",
        INVOICE_INVALID_DATE_MESSAGE: "invoice-invalid-date",
        INVOICE_REQUIRED_CONTACT_MESSAGE: "invoice-missing-contact",
    },
    "payments": {
        PAYMENT_INVALID_AMOUNT_MESSAGE: "payment-invalid-amount",
        PAYMENT_MATCH_INVALID_MESSAGE: "payment-invalid-match",
        PAYMENT_MISSING_MATCH_MESSAGE: "payment-unmatched",
        PAYMENT_REQUIRED_REFERENCE_OR_CONTACT_MESSAGE: "payment-missing-reference-or-contact",
        PAYMENT_UNMATCHABLE_MESSAGE: "payment-unmatched",
    },
}

_ISSUE_KIND_PREFIXES = {
    "bank": "bank",
    "cash": "cash",
    "contacts": "contact",
    "entries": "entry",
    "invoices": "invoice",
    "payments": "payment",
}

_GESTION_PREVIEW_HEADER_MARKERS = {
    "contacts": (("nom", "prenom"), ("nom", "email")),
    "payments": (("montant", "date"), ("montant", "facture")),
    "bank": (("date", "montant"), ("date", "debit")),
    "cash": (("date", "entree"), ("date", "montant")),
    "invoices": (("montant", "date"), ("montant", "client")),
}


def should_ignore_invoice_total_row(
    row: tuple[Any, ...],
    *,
    contact_name: str,
    row_contains_text: Callable[[tuple[Any, ...], str], bool],
) -> bool:
    """Return True when the row is an invoice total line without a customer."""
    return not contact_name and row_contains_text(row, "total")


def detect_gestion_preview_header(
    ws: Any,
    kind: str,
    *,
    detect_header_row: Callable[[Any, list[str]], Any],
) -> Any:
    """Try the stable preview header signatures for a gestion sheet kind."""
    for markers in _GESTION_PREVIEW_HEADER_MARKERS.get(
        kind,
        _GESTION_PREVIEW_HEADER_MARKERS["invoices"],
    ):
        header_info = detect_header_row(ws, list(markers))
        if header_info is not None:
            return header_info
    return None


def should_ignore_cash_initial_balance_row(
    row: tuple[Any, ...],
    *,
    raw_amount: Decimal | None,
    row_contains_text: Callable[[tuple[Any, ...], str], bool],
) -> bool:
    """Return True when the row only describes the opening cash balance."""
    return raw_amount is None and row_contains_text(row, "solde")


def should_ignore_cash_pending_deposit_forecast(
    row: tuple[Any, ...],
    *,
    tiers_idx: int | None,
    libelle_idx: int | None,
    raw_amount: Decimal | None,
    get_row_value: Callable[[tuple[Any, ...], int | None], Any],
    parse_str: Callable[[Any], str],
    normalize_text: Callable[[str], str],
) -> bool:
    """Return True when the row is an undated cash deposit forecast."""
    if raw_amount is None or raw_amount >= 0:
        return False

    tiers_value = normalize_text(parse_str(get_row_value(row, tiers_idx)))
    label_value = normalize_text(parse_str(get_row_value(row, libelle_idx)))
    return "remise especes" in label_value and any(
        marker in tiers_value for marker in ("credit mutuel", "banque", "bank")
    )


def should_ignore_bank_balance_description(
    *,
    entry_date: Any,
    amount: Decimal | None,
    label: str,
    balance: Decimal | None,
) -> bool:
    """Return True when the row only documents a balance without a movement."""
    return (
        entry_date is None
        and amount in (None, Decimal("0"))
        and bool(label)
        and balance is not None
    )


def should_ignore_zero_journal_entry(*, debit: Decimal, credit: Decimal) -> bool:
    """Return True when an accounting row carries no debit and no credit."""
    return debit == 0 and credit == 0


def invoice_missing_columns(
    *,
    date_idx: int | None,
    montant_idx: int | None,
    nom_idx: int | None,
) -> list[str]:
    """Return the missing required invoice columns for the current sheet."""
    missing_columns: list[str] = []
    if date_idx is None:
        missing_columns.append(INVOICE_REQUIRED_COLUMNS[0])
    if montant_idx is None:
        missing_columns.append(INVOICE_REQUIRED_COLUMNS[1])
    if nom_idx is None:
        missing_columns.append(INVOICE_REQUIRED_COLUMNS[2])
    return missing_columns


def payment_missing_columns(
    *,
    montant_idx: int | None,
    invoice_idx: int | None,
    nom_idx: int | None,
) -> list[str]:
    """Return the missing required payment columns for the current sheet."""
    missing_columns: list[str] = []
    if montant_idx is None:
        missing_columns.append(PAYMENT_REQUIRED_COLUMNS[0])
    if invoice_idx is None and nom_idx is None:
        missing_columns.append(PAYMENT_REQUIRED_COLUMNS[1])
    return missing_columns


def contact_missing_columns(*, nom_idx: int | None) -> list[str]:
    """Return the missing required contact columns for the current sheet."""
    return [CONTACT_REQUIRED_NAME_MESSAGE] if nom_idx is None else []


def cash_missing_columns(
    *,
    date_idx: int | None,
    entree_idx: int | None,
    sortie_idx: int | None,
    montant_idx: int | None,
) -> list[str]:
    """Return the missing required cash columns for the current sheet."""
    missing_columns: list[str] = []
    if date_idx is None:
        missing_columns.append(CASH_REQUIRED_DATE_OR_AMOUNT_COLUMNS[0])
    if entree_idx is None and sortie_idx is None and montant_idx is None:
        missing_columns.append(CASH_REQUIRED_DATE_OR_AMOUNT_COLUMNS[1])
    return missing_columns


def bank_missing_columns(
    *,
    date_idx: int | None,
    debit_idx: int | None,
    credit_idx: int | None,
    montant_idx: int | None,
) -> list[str]:
    """Return the missing required bank columns for the current sheet."""
    missing_columns: list[str] = []
    if date_idx is None:
        missing_columns.append(BANK_REQUIRED_DATE_OR_AMOUNT_COLUMNS[0])
    if debit_idx is None and credit_idx is None and montant_idx is None:
        missing_columns.append(BANK_REQUIRED_DATE_OR_AMOUNT_COLUMNS[1])
    return missing_columns


def entries_missing_columns(
    *,
    compte_idx: int | None,
    debit_idx: int | None,
    credit_idx: int | None,
) -> list[str]:
    """Return the missing required journal columns for the current sheet."""
    missing_columns: list[str] = []
    if compte_idx is None:
        missing_columns.append(ENTRY_REQUIRED_ACCOUNT_OR_AMOUNT_COLUMNS[0])
    if debit_idx is None and credit_idx is None:
        missing_columns.append(ENTRY_REQUIRED_ACCOUNT_OR_AMOUNT_COLUMNS[1])
    return missing_columns


def make_validation_issue(
    source_row_number: int,
    messages: list[str],
) -> RowValidationIssue:
    """Build a blocking row issue from one or more stable validation messages."""
    return RowValidationIssue(
        source_row_number=source_row_number,
        message="; ".join(messages),
    )


def format_source_row_issue(source_row_number: int, message: str) -> str:
    """Build the stable display string for a row-scoped issue."""
    return f"Ligne {source_row_number} : {message}"


def format_row_issue(issue: RowValidationIssue | RowIgnoredIssue) -> str:
    """Build the stable display string for a typed row issue."""
    return format_source_row_issue(issue.source_row_number, issue.message)


def format_missing_columns_issue(missing_columns: list[str]) -> str:
    """Build the stable display string for missing required columns."""
    return f"{MISSING_REQUIRED_COLUMNS_MESSAGE_PREFIX}: {', '.join(missing_columns)}"


def format_payment_blocked_issue(source_row_number: int, message: str | None) -> str:
    """Build the stable display string for a blocked payment row."""
    return format_source_row_issue(
        source_row_number,
        message or PAYMENT_UNMATCHABLE_MESSAGE,
    )


def make_payment_resolution_issue(
    *,
    source_row_number: int,
    status: str,
    candidate: Any | None,
    message: str | None,
    require_persistable_candidate: bool,
) -> RowValidationIssue | None:
    """Return the blocking payment issue implied by a match resolution, if any."""
    if status != "matched" or candidate is None:
        return RowValidationIssue(
            source_row_number=source_row_number,
            message=message or PAYMENT_UNMATCHABLE_MESSAGE,
        )

    if require_persistable_candidate and (
        getattr(candidate, "invoice_id", None) is None
        or getattr(candidate, "contact_id", None) is None
    ):
        return RowValidationIssue(
            source_row_number=source_row_number,
            message=PAYMENT_MATCH_INVALID_MESSAGE,
        )

    return None


def issue_category_for_message(
    message: str,
    *,
    kind: str | None = None,
    row_number: int | None = None,
    severity: str | None = None,
) -> str | None:
    """Return a stable category for a known issue message when available."""
    if message.startswith(ALREADY_IMPORTED_MESSAGE_PREFIX):
        return "already-imported"
    if message.startswith(COMPTABILITE_COEXISTENCE_BLOCKED_MESSAGE_PREFIX):
        return "comptabilite-coexistence-blocked"
    if message.startswith(IMPORT_ERROR_MESSAGE_PREFIX):
        return "import-error"
    if kind is not None and message.startswith(f"{MISSING_REQUIRED_COLUMNS_MESSAGE_PREFIX}:"):
        kind_prefix = _ISSUE_KIND_PREFIXES.get(kind)
        if kind_prefix is not None:
            return f"{kind_prefix}-missing-columns"
    if message.startswith(f"{MISSING_REQUIRED_COLUMNS_MESSAGE_PREFIX}:"):
        return "missing-columns"
    if kind is not None:
        category = _ISSUE_CATEGORY_BY_KIND_AND_MESSAGE.get(kind, {}).get(message)
        if category is not None:
            return category
    category = _UNAMBIGUOUS_ISSUE_CATEGORY_BY_MESSAGE.get(message)
    if category is not None:
        return category
    if severity == "error" and row_number is not None and kind is not None:
        kind_prefix = _ISSUE_KIND_PREFIXES.get(kind)
        if kind_prefix is not None:
            return f"{kind_prefix}-validation-error"
    return None


def filter_duplicate_rows(
    rows: list[RowType],
    *,
    identity_key: Callable[[RowType], str],
    source_row_number: Callable[[RowType], int],
    duplicate_message: str,
) -> tuple[list[RowType], list[tuple[int, str]]]:
    """Keep the first row for each identity key and report ignored duplicates."""
    seen: set[str] = set()
    kept_rows: list[RowType] = []
    ignored_rows: list[tuple[int, str]] = []
    for row in rows:
        row_key = identity_key(row)
        if row_key in seen:
            ignored_rows.append((source_row_number(row), duplicate_message))
            continue
        seen.add(row_key)
        kept_rows.append(row)
    return kept_rows, ignored_rows


def filter_duplicate_contact_rows(
    contact_rows: list[NormalizedContactRow],
    *,
    normalize_text: Callable[[str], str],
) -> tuple[list[NormalizedContactRow], list[RowIgnoredIssue]]:
    """Keep the first contact row for a given normalized nom/prenom identity."""
    kept_rows, ignored_rows = filter_duplicate_rows(
        contact_rows,
        identity_key=lambda row: "::".join(
            (
                normalize_text(row.nom),
                normalize_text(row.prenom or ""),
            )
        ),
        source_row_number=lambda row: row.source_row_number,
        duplicate_message=DUPLICATE_CONTACT_MESSAGE,
    )
    return kept_rows, [
        RowIgnoredIssue(source_row_number=source_row_number, message=message)
        for source_row_number, message in ignored_rows
    ]


def filter_duplicate_invoice_rows(
    invoice_rows: list[NormalizedInvoiceRow],
    *,
    normalize_text: Callable[[str], str],
) -> tuple[list[NormalizedInvoiceRow], list[RowIgnoredIssue]]:
    """Keep all unnumbered rows and the first numbered invoice row per normalized number."""
    numbered_rows = [invoice_row for invoice_row in invoice_rows if invoice_row.invoice_number]
    unnumbered_rows = [
        invoice_row for invoice_row in invoice_rows if not invoice_row.invoice_number
    ]
    kept_numbered_rows, ignored_rows = filter_duplicate_rows(
        numbered_rows,
        identity_key=lambda row: normalize_text(row.invoice_number or ""),
        source_row_number=lambda row: row.source_row_number,
        duplicate_message=DUPLICATE_INVOICE_MESSAGE,
    )
    kept_rows = unnumbered_rows + kept_numbered_rows
    kept_rows.sort(key=lambda row: row.source_row_number)
    return kept_rows, [
        RowIgnoredIssue(source_row_number=source_row_number, message=message)
        for source_row_number, message in ignored_rows
    ]


def make_existing_contact_issue(source_row_number: int) -> RowIgnoredIssue:
    """Build the stable ignored-row issue for a contact already present in DB."""
    return RowIgnoredIssue(
        source_row_number=source_row_number,
        message=EXISTING_CONTACT_MESSAGE,
    )


def make_existing_invoice_issue(source_row_number: int) -> RowIgnoredIssue:
    """Build the stable ignored-row issue for an invoice already present in DB."""
    return RowIgnoredIssue(
        source_row_number=source_row_number,
        message=EXISTING_INVOICE_MESSAGE,
    )


def find_existing_contact_issues(
    contact_rows: list[NormalizedContactRow],
    existing_contact_keys: set[str],
    *,
    contact_preview_key: Callable[[str, str | None], str],
) -> list[RowIgnoredIssue]:
    """Return ignored-row issues for contact rows already present in DB."""
    return [
        make_existing_contact_issue(contact_row.source_row_number)
        for contact_row in contact_rows
        if contact_preview_key(contact_row.nom, contact_row.prenom) in existing_contact_keys
    ]


def find_existing_invoice_issues(
    invoice_rows: list[NormalizedInvoiceRow],
    existing_invoice_numbers: set[str],
    *,
    normalize_text: Callable[[str], str],
) -> list[RowIgnoredIssue]:
    """Return ignored-row issues for invoice rows already present in DB."""
    issues: list[RowIgnoredIssue] = []
    for invoice_row in invoice_rows:
        if not invoice_row.invoice_number:
            continue
        if normalize_text(invoice_row.invoice_number) not in existing_invoice_numbers:
            continue
        issues.append(make_existing_invoice_issue(invoice_row.source_row_number))
    return issues


def make_invoice_ambiguous_contact_issue(source_row_number: int) -> RowValidationIssue:
    """Build the stable blocking issue for an invoice matching several contacts."""
    return RowValidationIssue(
        source_row_number=source_row_number,
        message=INVOICE_AMBIGUOUS_CONTACT_MESSAGE,
    )


def resolve_invoice_contact_match(
    invoice_row: NormalizedInvoiceRow,
    existing_contacts_by_key: dict[str, list[Any]],
    *,
    normalize_text: Callable[[str], str],
) -> tuple[Any | None, RowValidationIssue | None]:
    """Resolve an invoice contact against existing contacts with strict ambiguity handling."""
    contact_matches = existing_contacts_by_key.get(
        normalize_text(invoice_row.contact_name),
        [],
    )
    if len(contact_matches) == 1:
        return contact_matches[0], None
    if len(contact_matches) > 1:
        return None, make_invoice_ambiguous_contact_issue(invoice_row.source_row_number)
    return None, None


def find_ambiguous_invoice_contact_issues(
    invoice_rows: list[NormalizedInvoiceRow],
    existing_contacts_by_key: dict[str, list[Any]],
    *,
    normalize_text: Callable[[str], str],
) -> list[RowValidationIssue]:
    """Return blocking issues for invoice rows matching several existing contacts."""
    issues: list[RowValidationIssue] = []
    for invoice_row in invoice_rows:
        _, issue = resolve_invoice_contact_match(
            invoice_row,
            existing_contacts_by_key,
            normalize_text=normalize_text,
        )
        if issue is not None:
            issues.append(issue)
    return issues


def preview_warning_for_gestion_reason(reason: str | None) -> str | None:
    """Map a gestion preview ignore reason to a stable warning message."""
    if reason is None:
        return None
    return {
        "auxiliary-sheet": GESTION_AUXILIARY_SHEET_MESSAGE,
        "unmapped-sheet": UNMAPPED_SHEET_MESSAGE,
    }.get(reason)


def preview_warning_for_comptabilite_reason(reason: str | None) -> str | None:
    """Map a comptabilite preview ignore reason to a stable warning message."""
    if reason is None:
        return None
    return {
        "report-sheet": COMPTABILITE_REPORT_SHEET_MESSAGE,
        "entry-helper-sheet": COMPTABILITE_ENTRY_HELPER_SHEET_MESSAGE,
        "unmapped-sheet": UNMAPPED_SHEET_MESSAGE,
    }.get(reason)
