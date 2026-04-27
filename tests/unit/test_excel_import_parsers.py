"""Unit tests for Excel import worksheet parsers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from backend.services.excel_import_parsers import (
    parse_bank_sheet,
    parse_cash_sheet,
    parse_contact_sheet,
    parse_entries_sheet,
    parse_invoice_sheet,
    parse_payment_sheet,
)
from backend.services.excel_import_policy import (
    BANK_BALANCE_DESCRIPTION_MESSAGE,
    CASH_INITIAL_BALANCE_MESSAGE,
    CASH_PENDING_DEPOSIT_MESSAGE,
    INVOICE_INVALID_COMPONENT_BREAKDOWN_MESSAGE,
    INVOICE_INVALID_DATE_MESSAGE,
    INVOICE_TOTAL_MESSAGE,
    ZERO_JOURNAL_ENTRY_MESSAGE,
)
from backend.services.excel_import_types import RowValidationIssue


def _make_sheet(title: str, rows: list[list[object | None]]) -> Worksheet:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = title
    for row in rows:
        sheet.append(row)
    return sheet


def test_parse_invoice_sheet_reports_blocked_and_ignored_rows() -> None:
    sheet = _make_sheet(
        "Factures",
        [
            ["Date facture", "Réf facture", "Client", "Montant", "Type"],
            ["2025-08-01", "2025-0142", "Christine LOPES", 55, "CS"],
            ["2025-08-02", "2025-0143", None, 42, "A"],
            ["Total", None, None, 97, None],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_invoice_sheet(sheet)

    assert parsed_sheet is not None
    assert parsed_sheet.missing_columns == []
    assert len(rows) == 1
    assert rows[0].invoice_number == "2025-0142"
    assert rows[0].label == "cs"
    assert issues[0].source_row_number == 3
    assert issues[0].message == "client manquant"
    assert ignored_issues[0].source_row_number == 4
    assert ignored_issues[0].message == INVOICE_TOTAL_MESSAGE


def test_parse_invoice_sheet_blocks_missing_or_invalid_invoice_date() -> None:
    sheet = _make_sheet(
        "Factures",
        [
            ["Date facture", "Réf facture", "Client", "Montant"],
            [None, "2025-0142", "Christine LOPES", 55],
            ["not-a-date", "2025-0143", "Christine LOPES", 42],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_invoice_sheet(sheet)

    assert parsed_sheet is not None
    assert rows == []
    assert ignored_issues == []
    assert [issue.source_row_number for issue in issues] == [2, 3]
    assert [issue.message for issue in issues] == [
        INVOICE_INVALID_DATE_MESSAGE,
        INVOICE_INVALID_DATE_MESSAGE,
    ]


def test_parse_invoice_sheet_extracts_optional_cs_a_components() -> None:
    sheet = _make_sheet(
        "Factures",
        [
            [
                "Date facture",
                "Réf facture",
                "Client",
                "Montant",
                "Montant cours",
                "Montant adhésion",
                "Type",
            ],
            ["2025-08-01", "2025-0142", "Christine LOPES", 160, 130, 30, "CS+A"],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_invoice_sheet(sheet)

    assert parsed_sheet is not None
    assert issues == []
    assert ignored_issues == []
    assert len(rows) == 1
    assert rows[0].label == "cs+a"
    assert rows[0].course_amount == Decimal("130")
    assert rows[0].adhesion_amount == Decimal("30")


def test_parse_invoice_sheet_accepts_zero_value_cs_a_component() -> None:
    sheet = _make_sheet(
        "Factures",
        [
            [
                "Date facture",
                "Réf facture",
                "Client",
                "Montant",
                "Montant cours",
                "Montant adhésion",
                "Type",
            ],
            ["2025-08-01", "2025-0142", "Christine LOPES", 160, 160, 0, "CS+A"],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_invoice_sheet(sheet)

    assert parsed_sheet is not None
    assert issues == []
    assert ignored_issues == []
    assert len(rows) == 1
    assert rows[0].course_amount == Decimal("160")
    assert rows[0].adhesion_amount == Decimal("0")


def test_parse_invoice_sheet_blocks_inconsistent_explicit_cs_a_components() -> None:
    sheet = _make_sheet(
        "Factures",
        [
            [
                "Date facture",
                "Réf facture",
                "Client",
                "Montant",
                "Montant cours",
                "Montant adhésion",
                "Type",
            ],
            ["2025-08-01", "2025-0142", "Christine LOPES", 160, 120, 30, "CS+A"],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_invoice_sheet(sheet)

    assert parsed_sheet is not None
    assert rows == []
    assert ignored_issues == []
    assert issues == [
        RowValidationIssue(
            source_row_number=2,
            message=INVOICE_INVALID_COMPONENT_BREAKDOWN_MESSAGE,
        )
    ]


def test_parse_payment_sheet_normalizes_payment_fields() -> None:
    sheet = _make_sheet(
        "Paiements",
        [
            [
                "Réf facture",
                "Adhérent",
                "Montant",
                "Date paiement",
                "Mode de règlement",
                "Numéro du chèque",
                "Encaissé",
                "Date encaissement",
            ],
            [
                "2025-0142",
                "Christine LOPES",
                55,
                "2025-08-02",
                "Chèque",
                "CHK-001",
                "oui",
                "2025-08-05",
            ],
            [None, None, 40, "2025-08-03", "Virement", None, None, None],
        ],
    )

    parsed_sheet, rows, issues = parse_payment_sheet(sheet)

    assert parsed_sheet is not None
    assert parsed_sheet.missing_columns == []
    assert len(rows) == 1
    assert rows[0].method == "cheque"
    assert rows[0].cheque_number == "CHK-001"
    assert rows[0].deposited is True
    assert rows[0].deposit_date == date(2025, 8, 5)
    assert issues[0].source_row_number == 3
    assert issues[0].message == "reference facture ou contact manquant"


def test_parse_contact_sheet_accepts_missing_prenom_but_blocks_missing_nom() -> None:
    sheet = _make_sheet(
        "Contacts",
        [
            ["Nom", "Email"],
            ["Christine LOPES", "christine@example.test"],
            [None, "missing@example.test"],
        ],
    )

    parsed_sheet, rows, issues = parse_contact_sheet(sheet)

    assert parsed_sheet is not None
    assert len(rows) == 1
    assert rows[0].nom == "LOPES"
    assert rows[0].prenom == "Christine"
    assert rows[0].email == "christine@example.test"
    assert issues[0].source_row_number == 3
    assert issues[0].message == "nom manquant"


def test_parse_contact_sheet_splits_full_name_when_prenom_is_embedded_in_nom() -> None:
    sheet = _make_sheet(
        "Contacts",
        [
            ["Nom", "Email"],
            ["Christine LOPES", "christine@example.test"],
            ["Thi BE NGUYEN", "thi@example.test"],
            ["ASSOCIATION ABC", "asso@example.test"],
        ],
    )

    parsed_sheet, rows, issues = parse_contact_sheet(sheet)

    assert parsed_sheet is not None
    assert issues == []
    assert [(row.nom, row.prenom) for row in rows] == [
        ("LOPES", "Christine"),
        ("BE NGUYEN", "Thi"),
        ("ASSOCIATION ABC", None),
    ]


def test_parse_cash_sheet_ignores_safe_rows_and_parses_signed_amount() -> None:
    sheet = _make_sheet(
        "Caisse",
        [
            ["Date", "Montant", "Type", "Tiers", "Libellé"],
            [None, None, None, None, "Solde initial"],
            [None, -710, None, "Credit Mutuel", "Remise especes en attente"],
            ["2025-08-04", -20, None, "Papeterie", "Achat fournitures"],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_cash_sheet(sheet)

    assert parsed_sheet is not None
    assert issues == []
    assert len(rows) == 1
    assert rows[0].movement_type == "out"
    assert rows[0].amount == Decimal("20")
    assert rows[0].description == "Papeterie ; Achat fournitures"
    assert [issue.message for issue in ignored_issues] == [
        CASH_INITIAL_BALANCE_MESSAGE,
        CASH_PENDING_DEPOSIT_MESSAGE,
    ]


def test_parse_bank_sheet_ignores_balance_description_and_parses_credit_debit() -> None:
    sheet = _make_sheet(
        "Banque",
        [
            ["Date", "Libellé", "Débit", "Crédit", "Solde"],
            [None, "Solde au 01/01", None, None, 1250],
            ["2025-08-04", "Cotisation", None, 55, 1305],
            ["2025-08-05", "Prélèvement", 12, None, 1293],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_bank_sheet(sheet)

    assert parsed_sheet is not None
    assert issues == []
    assert len(rows) == 2
    assert rows[0].amount == Decimal("55")
    assert rows[1].amount == Decimal("-12")
    assert ignored_issues[0].message == BANK_BALANCE_DESCRIPTION_MESSAGE


def test_parse_entries_sheet_ignores_zero_rows_and_reports_invalid_amounts() -> None:
    sheet = _make_sheet(
        "Journal",
        [
            ["Date", "Compte", "Libellé", "Débit", "Crédit"],
            ["2025-08-04", "706000", "Cours", 0, 55],
            ["2025-08-05", "706000", "Zero", 0, 0],
            ["2025-08-06", "706000", "Erreur", "abc", None],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_entries_sheet(sheet)

    assert parsed_sheet is not None
    assert len(rows) == 1
    assert rows[0].account_number == "706000"
    assert rows[0].credit == Decimal("55")
    assert ignored_issues[0].message == ZERO_JOURNAL_ENTRY_MESSAGE
    assert issues[0].source_row_number == 4
    assert issues[0].message == "montant debit invalide"


def test_parse_entries_sheet_keeps_change_num_marker() -> None:
    sheet = _make_sheet(
        "Journal",
        [
            ["Date", "Compte", "Libellé", "Débit", "Crédit", "ChangeNum"],
            ["2025-08-04", "411100", "Facture 2025-0142", 55, None, 0],
            ["2025-08-04", "706000", "Facture 2025-0142", None, 55, 0],
            ["2025-08-05", "512000", "Banque", 40, None, 1],
        ],
    )

    parsed_sheet, rows, issues, ignored_issues = parse_entries_sheet(sheet)

    assert parsed_sheet is not None
    assert issues == []
    assert ignored_issues == []
    assert [row.change_marker for row in rows] == ["0", "0", "1"]
