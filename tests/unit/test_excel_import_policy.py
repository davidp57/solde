"""Unit tests for Excel import business policy helpers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

from backend.services.excel_import_policy import (
    BANK_BALANCE_DESCRIPTION_MESSAGE,
    BANK_INVALID_AMOUNT_MESSAGE,
    BANK_INVALID_DATE_MESSAGE,
    BANK_REQUIRED_DATE_OR_AMOUNT_COLUMNS,
    CASH_INITIAL_BALANCE_MESSAGE,
    CASH_INVALID_DATE_MESSAGE,
    CASH_INVALID_MOVEMENT_MESSAGE,
    CASH_PENDING_DEPOSIT_MESSAGE,
    CASH_REQUIRED_DATE_OR_AMOUNT_COLUMNS,
    COMPTABILITE_ENTRY_HELPER_SHEET_MESSAGE,
    COMPTABILITE_REPORT_SHEET_MESSAGE,
    COMPTABILITE_UNKNOWN_STRUCTURE_MESSAGE,
    CONTACT_REQUIRED_NAME_MESSAGE,
    DUPLICATE_CONTACT_MESSAGE,
    DUPLICATE_INVOICE_MESSAGE,
    ENTRY_INVALID_CREDIT_MESSAGE,
    ENTRY_INVALID_DATE_MESSAGE,
    ENTRY_INVALID_DEBIT_MESSAGE,
    ENTRY_MISSING_ACCOUNT_MESSAGE,
    ENTRY_REQUIRED_ACCOUNT_OR_AMOUNT_COLUMNS,
    EXISTING_CONTACT_MESSAGE,
    EXISTING_INVOICE_MESSAGE,
    GESTION_AUXILIARY_SHEET_MESSAGE,
    GESTION_UNKNOWN_STRUCTURE_MESSAGE,
    INVOICE_INVALID_AMOUNT_MESSAGE,
    INVOICE_INVALID_DATE_MESSAGE,
    INVOICE_REQUIRED_COLUMNS,
    INVOICE_REQUIRED_CONTACT_MESSAGE,
    INVOICE_TOTAL_MESSAGE,
    PAYMENT_INVALID_AMOUNT_MESSAGE,
    PAYMENT_MATCH_INVALID_MESSAGE,
    PAYMENT_MISSING_MATCH_MESSAGE,
    PAYMENT_REQUIRED_COLUMNS,
    PAYMENT_REQUIRED_REFERENCE_OR_CONTACT_MESSAGE,
    PAYMENT_UNMATCHABLE_MESSAGE,
    UNMAPPED_SHEET_MESSAGE,
    ZERO_JOURNAL_ENTRY_MESSAGE,
    bank_missing_columns,
    cash_missing_columns,
    contact_missing_columns,
    detect_gestion_preview_header,
    entries_missing_columns,
    filter_duplicate_contact_rows,
    filter_duplicate_invoice_rows,
    filter_duplicate_rows,
    find_ambiguous_invoice_contact_issues,
    find_existing_contact_issues,
    find_existing_invoice_issues,
    format_missing_columns_issue,
    format_payment_blocked_issue,
    format_row_issue,
    invoice_missing_columns,
    issue_category_for_message,
    make_existing_contact_issue,
    make_existing_invoice_issue,
    make_invoice_ambiguous_contact_issue,
    make_payment_resolution_issue,
    make_validation_issue,
    payment_missing_columns,
    preview_warning_for_comptabilite_reason,
    preview_warning_for_gestion_reason,
    resolve_invoice_contact_match,
    should_ignore_bank_balance_description,
    should_ignore_cash_initial_balance_row,
    should_ignore_cash_pending_deposit_forecast,
    should_ignore_invoice_total_row,
    should_ignore_zero_journal_entry,
)
from backend.services.excel_import_types import (
    NormalizedContactRow,
    NormalizedInvoiceRow,
    RowIgnoredIssue,
    RowValidationIssue,
)


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _parse_str(value: object | None) -> str:
    return "" if value is None else str(value).strip()


def _get_row_value(row: tuple[object, ...], index: int | None) -> object | None:
    return None if index is None or index >= len(row) else row[index]


def _row_contains_text(row: tuple[object, ...], *fragments: str) -> bool:
    normalized_cells = [_normalize_text(_parse_str(value)) for value in row]
    return any(
        _normalize_text(fragment) in cell for cell in normalized_cells for fragment in fragments
    )


def test_should_ignore_invoice_total_row_without_contact() -> None:
    row = ("", "Total general", Decimal("123.00"))
    assert should_ignore_invoice_total_row(
        row,
        contact_name="",
        row_contains_text=_row_contains_text,
    )
    assert INVOICE_TOTAL_MESSAGE == "ligne de total ignoree"


def test_should_not_ignore_invoice_total_row_when_contact_exists() -> None:
    row = ("Dupont", "Total general", Decimal("123.00"))
    assert not should_ignore_invoice_total_row(
        row,
        contact_name="Dupont",
        row_contains_text=_row_contains_text,
    )


def test_should_ignore_cash_initial_balance_row() -> None:
    row = ("Solde initial", None, None)
    assert should_ignore_cash_initial_balance_row(
        row,
        raw_amount=None,
        row_contains_text=_row_contains_text,
    )
    assert CASH_INITIAL_BALANCE_MESSAGE == "ligne de solde initial ignoree"


def test_should_ignore_cash_pending_deposit_forecast() -> None:
    row = (None, "Credit Mutuel", "Remise especes en attente")
    assert should_ignore_cash_pending_deposit_forecast(
        row,
        tiers_idx=1,
        libelle_idx=2,
        raw_amount=Decimal("-710"),
        get_row_value=_get_row_value,
        parse_str=_parse_str,
        normalize_text=_normalize_text,
    )
    assert CASH_PENDING_DEPOSIT_MESSAGE == "prevision de remise d'especes sans date, ligne ignoree"


def test_should_not_ignore_cash_pending_deposit_forecast_for_positive_amount() -> None:
    row = (None, "Credit Mutuel", "Remise especes en attente")
    assert not should_ignore_cash_pending_deposit_forecast(
        row,
        tiers_idx=1,
        libelle_idx=2,
        raw_amount=Decimal("710"),
        get_row_value=_get_row_value,
        parse_str=_parse_str,
        normalize_text=_normalize_text,
    )


def test_should_ignore_bank_balance_description() -> None:
    assert should_ignore_bank_balance_description(
        entry_date=None,
        amount=Decimal("0"),
        label="Solde au 01/01",
        balance=Decimal("1250.00"),
    )
    assert BANK_BALANCE_DESCRIPTION_MESSAGE == "ligne descriptive de solde ignoree"


def test_should_ignore_zero_journal_entry() -> None:
    assert should_ignore_zero_journal_entry(
        debit=Decimal("0"),
        credit=Decimal("0"),
    )
    assert ZERO_JOURNAL_ENTRY_MESSAGE == "ecriture a debit/credit nuls ignoree"


def test_detect_gestion_preview_header_tries_stable_signatures_for_contacts() -> None:
    tried_markers: list[tuple[str, ...]] = []

    def _detect_header_row(_ws: object, markers: list[str]) -> tuple[int, dict[str, int]] | None:
        tried_markers.append(tuple(markers))
        if tuple(markers) == ("nom", "email"):
            return 3, {"nom": 0, "email": 1}
        return None

    header_info = detect_gestion_preview_header(
        object(),
        "contacts",
        detect_header_row=_detect_header_row,
    )

    assert header_info == (3, {"nom": 0, "email": 1})
    assert tried_markers == [("nom", "prenom"), ("nom", "email")]


def test_detect_gestion_preview_header_uses_invoice_fallback_for_unknown_kind() -> None:
    tried_markers: list[tuple[str, ...]] = []

    def _detect_header_row(_ws: object, markers: list[str]) -> tuple[int, dict[str, int]] | None:
        tried_markers.append(tuple(markers))
        return None

    header_info = detect_gestion_preview_header(
        object(),
        "invoices",
        detect_header_row=_detect_header_row,
    )

    assert header_info is None
    assert tried_markers == [("montant", "date"), ("montant", "client")]


def test_filter_duplicate_rows_keeps_first_row_only() -> None:
    rows: list[dict[str, str | int]] = [
        {"row": 2, "key": "dupont"},
        {"row": 3, "key": "dupont"},
        {"row": 4, "key": "durand"},
    ]

    kept_rows, ignored_rows = filter_duplicate_rows(
        rows,
        identity_key=lambda row: str(row["key"]),
        source_row_number=lambda row: cast(int, row["row"]),
        duplicate_message=DUPLICATE_CONTACT_MESSAGE,
    )

    assert kept_rows == [rows[0], rows[2]]
    assert ignored_rows == [(3, DUPLICATE_CONTACT_MESSAGE)]


def test_filter_duplicate_contact_rows_uses_nom_and_prenom_identity() -> None:
    rows = [
        NormalizedContactRow(source_row_number=2, nom="Christine LOPES", prenom=None, email=None),
        NormalizedContactRow(
            source_row_number=3, nom="  christine   lopes ", prenom=None, email="dup@example.test"
        ),
        NormalizedContactRow(source_row_number=4, nom="Thi BE NGUYEN", prenom=None, email=None),
    ]

    kept_rows, ignored_issues = filter_duplicate_contact_rows(
        rows,
        normalize_text=_normalize_text,
    )

    assert kept_rows == [rows[0], rows[2]]
    assert len(ignored_issues) == 1
    assert ignored_issues[0].source_row_number == 3
    assert ignored_issues[0].message == DUPLICATE_CONTACT_MESSAGE


def test_filter_duplicate_invoice_rows_keeps_first_numbered_and_all_unnumbered() -> None:
    rows = [
        NormalizedInvoiceRow(
            source_row_number=2,
            invoice_date=date(2025, 8, 1),
            amount=Decimal("10"),
            contact_name="Christine LOPES",
            invoice_number="2025-0142",
            label="cs",
        ),
        NormalizedInvoiceRow(
            source_row_number=3,
            invoice_date=date(2025, 8, 2),
            amount=Decimal("11"),
            contact_name="Christine LOPES",
            invoice_number=None,
            label="cs",
        ),
        NormalizedInvoiceRow(
            source_row_number=4,
            invoice_date=date(2025, 8, 3),
            amount=Decimal("12"),
            contact_name="Christine LOPES",
            invoice_number=" 2025-0142 ",
            label="cs",
        ),
    ]

    kept_rows, ignored_issues = filter_duplicate_invoice_rows(
        rows,
        normalize_text=_normalize_text,
    )

    assert kept_rows == [rows[0], rows[1]]
    assert len(ignored_issues) == 1
    assert ignored_issues[0].source_row_number == 4
    assert ignored_issues[0].message == DUPLICATE_INVOICE_MESSAGE


def test_make_existing_row_issues_use_stable_messages() -> None:
    contact_issue = make_existing_contact_issue(12)
    invoice_issue = make_existing_invoice_issue(18)

    assert contact_issue.source_row_number == 12
    assert contact_issue.message == EXISTING_CONTACT_MESSAGE
    assert invoice_issue.source_row_number == 18
    assert invoice_issue.message == EXISTING_INVOICE_MESSAGE


def test_find_existing_contact_issues_uses_preview_key_matching() -> None:
    def _preview_key(nom: str | None, prenom: str | None = None) -> str:
        return _normalize_text(f"{prenom or ''} {nom}".strip())

    rows = [
        NormalizedContactRow(source_row_number=2, nom="LOPES", prenom="Christine", email=None),
        NormalizedContactRow(source_row_number=3, nom="BE NGUYEN", prenom="Thi", email=None),
    ]

    ignored_issues = find_existing_contact_issues(
        rows,
        {"christine lopes"},
        contact_preview_key=_preview_key,
    )

    assert ignored_issues == [make_existing_contact_issue(2)]


def test_find_existing_invoice_issues_matches_normalized_numbers_only() -> None:
    rows = [
        NormalizedInvoiceRow(
            source_row_number=2,
            invoice_date=date(2025, 8, 1),
            amount=Decimal("10"),
            contact_name="Christine LOPES",
            invoice_number="2025-0142",
            label="cs",
        ),
        NormalizedInvoiceRow(
            source_row_number=3,
            invoice_date=date(2025, 8, 2),
            amount=Decimal("11"),
            contact_name="Thi BE NGUYEN",
            invoice_number=" 2025-9999 ",
            label="cs",
        ),
        NormalizedInvoiceRow(
            source_row_number=4,
            invoice_date=date(2025, 8, 3),
            amount=Decimal("12"),
            contact_name="Sans Numero",
            invoice_number=None,
            label="cs",
        ),
    ]

    ignored_issues = find_existing_invoice_issues(
        rows,
        {"2025-0142", "2025-9999"},
        normalize_text=_normalize_text,
    )

    assert ignored_issues == [
        make_existing_invoice_issue(2),
        make_existing_invoice_issue(3),
    ]


def test_make_invoice_ambiguous_contact_issue_uses_stable_message() -> None:
    issue = make_invoice_ambiguous_contact_issue(8)

    assert issue.source_row_number == 8
    assert issue.message == "client ambigu : plusieurs contacts correspondent"


def test_find_ambiguous_invoice_contact_issues_blocks_only_ambiguous_matches() -> None:
    rows = [
        NormalizedInvoiceRow(
            source_row_number=2,
            invoice_date=date(2025, 8, 1),
            amount=Decimal("10"),
            contact_name="Alice Dupont",
            invoice_number="2025-0142",
            label="cs",
        ),
        NormalizedInvoiceRow(
            source_row_number=3,
            invoice_date=date(2025, 8, 2),
            amount=Decimal("11"),
            contact_name="Bob Martin",
            invoice_number="2025-0143",
            label="cs",
        ),
        NormalizedInvoiceRow(
            source_row_number=4,
            invoice_date=date(2025, 8, 3),
            amount=Decimal("12"),
            contact_name="Claire Durand",
            invoice_number="2025-0144",
            label="cs",
        ),
    ]

    issues = find_ambiguous_invoice_contact_issues(
        rows,
        {
            "alice dupont": [SimpleNamespace(id=1), SimpleNamespace(id=2)],
            "bob martin": [SimpleNamespace(id=3)],
        },
        normalize_text=_normalize_text,
    )

    assert issues == [make_invoice_ambiguous_contact_issue(2)]


def test_resolve_invoice_contact_match_returns_unique_contact_or_issue() -> None:
    row = NormalizedInvoiceRow(
        source_row_number=2,
        invoice_date=date(2025, 8, 1),
        amount=Decimal("10"),
        contact_name="Alice Dupont",
        invoice_number="2025-0142",
        label="cs",
    )

    matched_contact, matched_issue = resolve_invoice_contact_match(
        row,
        {"alice dupont": [SimpleNamespace(id=7)]},
        normalize_text=_normalize_text,
    )
    assert matched_contact is not None
    assert matched_contact.id == 7
    assert matched_issue is None

    missing_contact, missing_issue = resolve_invoice_contact_match(
        row,
        {},
        normalize_text=_normalize_text,
    )
    assert missing_contact is None
    assert missing_issue is None

    ambiguous_contact, ambiguous_issue = resolve_invoice_contact_match(
        row,
        {"alice dupont": [SimpleNamespace(id=7), SimpleNamespace(id=8)]},
        normalize_text=_normalize_text,
    )
    assert ambiguous_contact is None
    assert ambiguous_issue == make_invoice_ambiguous_contact_issue(2)


def test_issue_category_for_message_uses_global_prefixes() -> None:
    assert (
        issue_category_for_message("Fichier deja importe (gestion) le 2026-04-11 12:34:56")
        == "already-imported"
    )
    assert (
        issue_category_for_message(
            "Import comptabilite : des ecritures auto-generees "
            "issues de la gestion existent deja en base (2)."
        )
        == "comptabilite-coexistence"
    )
    assert issue_category_for_message("Erreur import gestion : boom") == "import-error"


def test_missing_columns_helpers_define_stable_sheet_contracts() -> None:
    assert invoice_missing_columns(date_idx=None, montant_idx=None, nom_idx=None) == list(
        INVOICE_REQUIRED_COLUMNS
    )
    assert payment_missing_columns(montant_idx=None, invoice_idx=None, nom_idx=None) == list(
        PAYMENT_REQUIRED_COLUMNS
    )
    assert contact_missing_columns(nom_idx=None) == [CONTACT_REQUIRED_NAME_MESSAGE]
    assert cash_missing_columns(
        date_idx=None, entree_idx=None, sortie_idx=None, montant_idx=None
    ) == list(CASH_REQUIRED_DATE_OR_AMOUNT_COLUMNS)
    assert bank_missing_columns(
        date_idx=None, debit_idx=None, credit_idx=None, montant_idx=None
    ) == list(BANK_REQUIRED_DATE_OR_AMOUNT_COLUMNS)
    assert entries_missing_columns(compte_idx=None, debit_idx=None, credit_idx=None) == list(
        ENTRY_REQUIRED_ACCOUNT_OR_AMOUNT_COLUMNS
    )


def test_make_validation_issue_uses_stable_joined_messages() -> None:
    issue = make_validation_issue(
        14,
        [
            INVOICE_INVALID_AMOUNT_MESSAGE,
            INVOICE_REQUIRED_CONTACT_MESSAGE,
        ],
    )

    assert issue == RowValidationIssue(
        source_row_number=14,
        message="montant manquant ou invalide; client manquant",
    )


def test_format_row_issue_uses_stable_display_contract() -> None:
    ignored_issue = RowIgnoredIssue(
        source_row_number=9,
        message=EXISTING_CONTACT_MESSAGE,
    )
    validation_issue = RowValidationIssue(
        source_row_number=14,
        message=INVOICE_REQUIRED_CONTACT_MESSAGE,
    )

    assert format_row_issue(ignored_issue) == "Ligne 9 : contact deja existant, ligne ignoree"
    assert format_row_issue(validation_issue) == "Ligne 14 : client manquant"


def test_format_missing_columns_issue_uses_stable_display_contract() -> None:
    assert format_missing_columns_issue(["date", "montant"]) == (
        "Colonnes requises manquantes: date, montant"
    )


def test_format_payment_blocked_issue_uses_stable_messages() -> None:
    assert format_payment_blocked_issue(6, PAYMENT_MISSING_MATCH_MESSAGE) == (
        "Ligne 6 : paiement impossible a rapprocher a une facture existante ou importee"
    )
    assert format_payment_blocked_issue(7, None) == "Ligne 7 : paiement non rapprochable"
    assert format_payment_blocked_issue(8, PAYMENT_MATCH_INVALID_MESSAGE) == (
        "Ligne 8 : paiement rapproche sans identifiant exploitable"
    )


def test_make_payment_resolution_issue_blocks_unmatched_payment_for_preview() -> None:
    issue = make_payment_resolution_issue(
        source_row_number=6,
        status="missing",
        candidate=None,
        message=PAYMENT_MISSING_MATCH_MESSAGE,
        require_persistable_candidate=False,
    )

    assert issue == RowValidationIssue(
        source_row_number=6,
        message=PAYMENT_MISSING_MATCH_MESSAGE,
    )


def test_make_payment_resolution_issue_accepts_workbook_match_for_preview() -> None:
    issue = make_payment_resolution_issue(
        source_row_number=7,
        status="matched",
        candidate=SimpleNamespace(invoice_id=None, contact_id=None),
        message=None,
        require_persistable_candidate=False,
    )

    assert issue is None


def test_make_payment_resolution_issue_blocks_non_persistable_match_for_import() -> None:
    issue = make_payment_resolution_issue(
        source_row_number=8,
        status="matched",
        candidate=SimpleNamespace(invoice_id=None, contact_id=3),
        message=None,
        require_persistable_candidate=True,
    )

    assert issue == RowValidationIssue(
        source_row_number=8,
        message=PAYMENT_MATCH_INVALID_MESSAGE,
    )


def test_validation_message_constants_cover_current_parser_contract() -> None:
    assert PAYMENT_INVALID_AMOUNT_MESSAGE == "montant manquant ou invalide"
    assert PAYMENT_REQUIRED_REFERENCE_OR_CONTACT_MESSAGE == "reference facture ou contact manquant"
    assert CASH_INVALID_DATE_MESSAGE == "date manquante ou invalide"
    assert CASH_INVALID_MOVEMENT_MESSAGE == "mouvement ou montant manquant/invalide"
    assert BANK_INVALID_DATE_MESSAGE == "date manquante ou invalide"
    assert BANK_INVALID_AMOUNT_MESSAGE == "montant manquant ou nul"
    assert ENTRY_INVALID_DATE_MESSAGE == "date invalide"
    assert ENTRY_MISSING_ACCOUNT_MESSAGE == "compte manquant"
    assert ENTRY_INVALID_DEBIT_MESSAGE == "montant debit invalide"
    assert ENTRY_INVALID_CREDIT_MESSAGE == "montant credit invalide"


def test_issue_category_for_message_returns_expected_stable_categories() -> None:
    assert issue_category_for_message(EXISTING_CONTACT_MESSAGE) == "existing-contact"
    assert issue_category_for_message(DUPLICATE_INVOICE_MESSAGE) == "duplicate-invoice"
    assert (
        issue_category_for_message(
            INVOICE_REQUIRED_CONTACT_MESSAGE,
            kind="invoices",
            row_number=3,
            severity="error",
        )
        == "invoice-missing-contact"
    )
    assert (
        issue_category_for_message(
            INVOICE_INVALID_DATE_MESSAGE,
            kind="invoices",
            row_number=3,
            severity="error",
        )
        == "invoice-invalid-date"
    )
    assert (
        issue_category_for_message(
            PAYMENT_MISSING_MATCH_MESSAGE,
            kind="payments",
            row_number=4,
            severity="error",
        )
        == "payment-unmatched"
    )
    assert (
        issue_category_for_message(
            PAYMENT_UNMATCHABLE_MESSAGE,
            kind="payments",
            row_number=4,
            severity="error",
        )
        == "payment-unmatched"
    )
    assert (
        issue_category_for_message(
            PAYMENT_MATCH_INVALID_MESSAGE,
            kind="payments",
            row_number=4,
            severity="error",
        )
        == "payment-invalid-match"
    )
    assert (
        issue_category_for_message(
            "Colonnes requises manquantes: date, montant",
            kind="payments",
            severity="error",
        )
        == "payment-missing-columns"
    )
    assert issue_category_for_message("Colonnes requises manquantes: date, montant") == (
        "missing-columns"
    )
    assert issue_category_for_message(GESTION_AUXILIARY_SHEET_MESSAGE) == "gestion-auxiliary-sheet"
    assert issue_category_for_message("message libre") is None


def test_issue_category_for_message_falls_back_to_kind_validation_error() -> None:
    assert (
        issue_category_for_message(
            "montant manquant",
            kind="invoices",
            row_number=2,
            severity="error",
        )
        == "invoice-validation-error"
    )
    assert (
        issue_category_for_message(
            "montant manquant ou invalide; client manquant",
            kind="invoices",
            row_number=14,
            severity="error",
        )
        == "invoice-validation-error"
    )


def test_preview_warning_for_gestion_reason_returns_expected_messages() -> None:
    assert preview_warning_for_gestion_reason("auxiliary-sheet") == GESTION_AUXILIARY_SHEET_MESSAGE
    assert preview_warning_for_gestion_reason("unmapped-sheet") == UNMAPPED_SHEET_MESSAGE
    assert preview_warning_for_gestion_reason("other") is None
    assert (
        GESTION_UNKNOWN_STRUCTURE_MESSAGE
        == "Structure non reconnue, feuille ignoree par la preview"
    )


def test_preview_warning_for_comptabilite_reason_returns_expected_messages() -> None:
    assert (
        preview_warning_for_comptabilite_reason("report-sheet") == COMPTABILITE_REPORT_SHEET_MESSAGE
    )
    assert (
        preview_warning_for_comptabilite_reason("entry-helper-sheet")
        == COMPTABILITE_ENTRY_HELPER_SHEET_MESSAGE
    )
    assert preview_warning_for_comptabilite_reason("unmapped-sheet") == UNMAPPED_SHEET_MESSAGE
    assert preview_warning_for_comptabilite_reason("other") is None
    assert (
        COMPTABILITE_UNKNOWN_STRUCTURE_MESSAGE
        == "Structure de journal non reconnue, feuille ignoree par la preview"
    )
