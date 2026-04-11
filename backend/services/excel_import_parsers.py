"""Worksheet parsers for historical Excel import."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from backend.services.excel_import_parsing import (
    is_truthy_yes,
    normalize_invoice_label,
    normalize_payment_method,
    normalize_text,
    parse_date,
    parse_decimal,
    parse_str,
)
from backend.services.excel_import_policy import (
    BANK_BALANCE_DESCRIPTION_MESSAGE,
    BANK_INVALID_AMOUNT_MESSAGE,
    BANK_INVALID_DATE_MESSAGE,
    CASH_INITIAL_BALANCE_MESSAGE,
    CASH_INVALID_DATE_MESSAGE,
    CASH_INVALID_MOVEMENT_MESSAGE,
    CASH_PENDING_DEPOSIT_MESSAGE,
    CONTACT_REQUIRED_NAME_MESSAGE,
    ENTRY_INVALID_CREDIT_MESSAGE,
    ENTRY_INVALID_DATE_MESSAGE,
    ENTRY_INVALID_DEBIT_MESSAGE,
    ENTRY_MISSING_ACCOUNT_MESSAGE,
    INVOICE_INVALID_AMOUNT_MESSAGE,
    INVOICE_INVALID_DATE_MESSAGE,
    INVOICE_REQUIRED_CONTACT_MESSAGE,
    INVOICE_TOTAL_MESSAGE,
    PAYMENT_INVALID_AMOUNT_MESSAGE,
    PAYMENT_REQUIRED_REFERENCE_OR_CONTACT_MESSAGE,
    ZERO_JOURNAL_ENTRY_MESSAGE,
    bank_missing_columns,
    cash_missing_columns,
    contact_missing_columns,
    entries_missing_columns,
    invoice_missing_columns,
    make_validation_issue,
    payment_missing_columns,
    should_ignore_bank_balance_description,
    should_ignore_cash_initial_balance_row,
    should_ignore_cash_pending_deposit_forecast,
    should_ignore_invoice_total_row,
    should_ignore_zero_journal_entry,
)
from backend.services.excel_import_sheet_helpers import (
    compose_description,
    detect_header_row,
    find_col_idx,
    find_invoice_number_idx,
    get_row_value,
    row_contains_text,
)
from backend.services.excel_import_types import (
    NormalizedBankRow,
    NormalizedCashRow,
    NormalizedContactRow,
    NormalizedEntryRow,
    NormalizedInvoiceRow,
    NormalizedPaymentRow,
    ParsedSheet,
    RowIgnoredIssue,
    RowValidationIssue,
)

_DATE_LIKE_TEXT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$|^\d{2}/\d{2}/\d{4}$|^\d{2}-\d{2}-\d{4}$"
)


def _is_cash_pending_deposit_forecast(
    row: tuple[Any, ...],
    *,
    tiers_idx: int | None,
    libelle_idx: int | None,
    raw_amount: Decimal | None,
) -> bool:
    return should_ignore_cash_pending_deposit_forecast(
        row,
        tiers_idx=tiers_idx,
        libelle_idx=libelle_idx,
        raw_amount=raw_amount,
        get_row_value=get_row_value,
        parse_str=parse_str,
        normalize_text=normalize_text,
    )


def parse_invoice_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedInvoiceRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    """Parse invoice rows into a shared normalized structure."""
    header_info = detect_header_row(ws, ["date", "montant", "client"])
    if header_info is None:
        return None, [], [], []

    header_row, col_map = header_info
    date_idx = find_col_idx(col_map, "date")
    montant_idx = find_col_idx(col_map, "montant", "total")
    nom_idx = find_col_idx(col_map, "nom", "client", "adhérent", "adherent")
    numero_idx = find_invoice_number_idx(col_map, exclude_idx=date_idx)
    label_idx = find_col_idx(col_map, "motif", "libellé", "libelle", "type")

    missing_columns = invoice_missing_columns(
        date_idx=date_idx,
        montant_idx=montant_idx,
        nom_idx=nom_idx,
    )

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, [], [], []

    rows: list[NormalizedInvoiceRow] = []
    issues: list[RowValidationIssue] = []
    ignored_issues: list[RowIgnoredIssue] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        amount = parse_decimal(get_row_value(row, montant_idx))
        contact_name = parse_str(get_row_value(row, nom_idx))
        if should_ignore_invoice_total_row(
            row,
            contact_name=contact_name,
            row_contains_text=row_contains_text,
        ):
            ignored_issues.append(
                RowIgnoredIssue(
                    source_row_number=source_row_number,
                    message=INVOICE_TOTAL_MESSAGE,
                )
            )
            continue

        row_errors: list[str] = []
        invoice_date = parse_date(get_row_value(row, date_idx))
        if amount is None or amount <= 0:
            row_errors.append(INVOICE_INVALID_AMOUNT_MESSAGE)
        if invoice_date is None:
            row_errors.append(INVOICE_INVALID_DATE_MESSAGE)
        if not contact_name:
            row_errors.append(INVOICE_REQUIRED_CONTACT_MESSAGE)
        if row_errors:
            issues.append(make_validation_issue(source_row_number, row_errors))
            continue

        assert amount is not None
        assert invoice_date is not None
        raw_number = get_row_value(row, numero_idx)
        invoice_number: str | None = None
        if not isinstance(raw_number, (date, datetime)):
            candidate = parse_str(raw_number)
            if candidate and not _DATE_LIKE_TEXT_RE.match(candidate):
                invoice_number = candidate

        rows.append(
            NormalizedInvoiceRow(
                source_row_number=source_row_number,
                invoice_date=invoice_date,
                amount=amount,
                contact_name=contact_name,
                invoice_number=invoice_number,
                label=normalize_invoice_label(get_row_value(row, label_idx)),
            )
        )

    return parsed_sheet, rows, issues, ignored_issues


def parse_payment_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedPaymentRow], list[RowValidationIssue]]:
    """Parse payment rows into a shared normalized structure."""
    header_info = detect_header_row(ws, ["montant", "date"])
    if header_info is None:
        header_info = detect_header_row(ws, ["montant", "facture"])
    if header_info is None:
        return None, [], []

    header_row, col_map = header_info
    date_idx = find_col_idx(col_map, "date paiement", "date")
    montant_idx = find_col_idx(col_map, "montant")
    mode_idx = find_col_idx(
        col_map,
        "mode",
        "règl",
        "regl",
        "réf paiement",
        "ref paiement",
    )
    invoice_idx = find_invoice_number_idx(col_map, exclude_idx=date_idx)
    nom_idx = find_col_idx(col_map, "nom", "client", "adhérent", "adherent")
    cheque_idx = find_col_idx(
        col_map,
        "numéro du chèque",
        "numero du cheque",
        "chèque",
        "cheque",
    )
    deposited_idx = find_col_idx(col_map, "encaissé", "encaisse")
    deposit_date_idx = find_col_idx(col_map, "date encaissement")

    missing_columns = payment_missing_columns(
        montant_idx=montant_idx,
        invoice_idx=invoice_idx,
        nom_idx=nom_idx,
    )

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, [], []

    rows: list[NormalizedPaymentRow] = []
    issues: list[RowValidationIssue] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        amount = parse_decimal(get_row_value(row, montant_idx))
        invoice_ref = parse_str(get_row_value(row, invoice_idx))
        contact_name = parse_str(get_row_value(row, nom_idx))

        row_errors: list[str] = []
        if amount is None or amount <= 0:
            row_errors.append(PAYMENT_INVALID_AMOUNT_MESSAGE)
        if not invoice_ref and not contact_name:
            row_errors.append(PAYMENT_REQUIRED_REFERENCE_OR_CONTACT_MESSAGE)
        if row_errors:
            issues.append(make_validation_issue(source_row_number, row_errors))
            continue

        assert amount is not None
        rows.append(
            NormalizedPaymentRow(
                source_row_number=source_row_number,
                payment_date=parse_date(get_row_value(row, date_idx)) or date.today(),
                amount=amount,
                method=normalize_payment_method(get_row_value(row, mode_idx)),
                invoice_ref=invoice_ref,
                contact_name=contact_name,
                cheque_number=parse_str(get_row_value(row, cheque_idx)) or None,
                deposited=is_truthy_yes(get_row_value(row, deposited_idx)),
                deposit_date=parse_date(get_row_value(row, deposit_date_idx)),
            )
        )

    return parsed_sheet, rows, issues


def parse_contact_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedContactRow], list[RowValidationIssue]]:
    """Parse contact rows into a shared normalized structure."""
    header_info = detect_header_row(ws, ["nom", "prenom"])
    if header_info is None:
        header_info = detect_header_row(ws, ["nom", "email"])
    if header_info is None:
        header_info = detect_header_row(ws, ["nom", "mail"])
    if header_info is None:
        return None, [], []

    header_row, col_map = header_info
    nom_idx = find_col_idx(col_map, "nom")
    prenom_idx = find_col_idx(col_map, "prenom", "prénom")
    email_idx = find_col_idx(col_map, "email", "mail")

    missing_columns = contact_missing_columns(nom_idx=nom_idx)

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, [], []

    rows: list[NormalizedContactRow] = []
    issues: list[RowValidationIssue] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        nom = parse_str(get_row_value(row, nom_idx))
        if not nom:
            issues.append(
                make_validation_issue(
                    source_row_number,
                    [f"{CONTACT_REQUIRED_NAME_MESSAGE} manquant"],
                )
            )
            continue

        prenom = parse_str(get_row_value(row, prenom_idx)) or None
        email = parse_str(get_row_value(row, email_idx)) or None
        rows.append(
            NormalizedContactRow(
                source_row_number=source_row_number,
                nom=nom,
                prenom=prenom,
                email=email,
            )
        )

    return parsed_sheet, rows, issues


def parse_cash_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedCashRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    """Parse cash rows into a shared normalized structure."""
    header_info = detect_header_row(ws, ["date", "entree"])
    if header_info is None:
        header_info = detect_header_row(ws, ["date", "sortie"])
    if header_info is None:
        header_info = detect_header_row(ws, ["date", "montant"])
    if header_info is None:
        return None, [], [], []

    header_row, col_map = header_info
    date_idx = find_col_idx(col_map, "date")
    entree_idx = find_col_idx(col_map, "entree", "entrée", "recette", "credit", "crédit")
    sortie_idx = find_col_idx(col_map, "sortie", "depense", "dépense", "debit", "débit")
    montant_idx = (
        find_col_idx(col_map, "montant", "total")
        if entree_idx is None and sortie_idx is None
        else None
    )
    type_idx = find_col_idx(col_map, "type", "sens") if montant_idx is not None else None
    libelle_idx = find_col_idx(col_map, "libel", "descr", "label", "objet", "comment")
    tiers_idx = find_col_idx(col_map, "tiers", "tier", "benef")

    missing_columns = cash_missing_columns(
        date_idx=date_idx,
        entree_idx=entree_idx,
        sortie_idx=sortie_idx,
        montant_idx=montant_idx,
    )

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, [], [], []

    rows: list[NormalizedCashRow] = []
    issues: list[RowValidationIssue] = []
    ignored_issues: list[RowIgnoredIssue] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        raw_amount = (
            parse_decimal(get_row_value(row, montant_idx)) if montant_idx is not None else None
        )
        entry_date = parse_date(get_row_value(row, date_idx))
        if should_ignore_cash_initial_balance_row(
            row,
            raw_amount=raw_amount,
            row_contains_text=row_contains_text,
        ):
            ignored_issues.append(
                RowIgnoredIssue(
                    source_row_number=source_row_number,
                    message=CASH_INITIAL_BALANCE_MESSAGE,
                )
            )
            continue
        if entry_date is None and _is_cash_pending_deposit_forecast(
            row,
            tiers_idx=tiers_idx,
            libelle_idx=libelle_idx,
            raw_amount=raw_amount,
        ):
            ignored_issues.append(
                RowIgnoredIssue(
                    source_row_number=source_row_number,
                    message=CASH_PENDING_DEPOSIT_MESSAGE,
                )
            )
            continue
        if entry_date is None:
            issues.append(make_validation_issue(source_row_number, [CASH_INVALID_DATE_MESSAGE]))
            continue

        amount: Decimal | None = None
        movement_type: str | None = None
        if entree_idx is not None or sortie_idx is not None:
            entree = parse_decimal(get_row_value(row, entree_idx))
            sortie = parse_decimal(get_row_value(row, sortie_idx))
            if entree is not None and entree > 0:
                amount = entree
                movement_type = "in"
            elif sortie is not None and sortie > 0:
                amount = sortie
                movement_type = "out"
        elif montant_idx is not None:
            amount = raw_amount
            raw_type = normalize_text(parse_str(get_row_value(row, type_idx)))
            if raw_type in ("e", "in", "entree", "recette", "credit"):
                amount = abs(amount) if amount is not None else None
                movement_type = "in"
            elif raw_type in ("s", "out", "sortie", "depense", "debit"):
                amount = abs(amount) if amount is not None else None
                movement_type = "out"
            elif amount is not None and amount > 0:
                movement_type = "in"
            elif amount is not None and amount < 0:
                amount = abs(amount)
                movement_type = "out"

        if amount is None or amount <= 0 or movement_type is None:
            issues.append(make_validation_issue(source_row_number, [CASH_INVALID_MOVEMENT_MESSAGE]))
            continue

        rows.append(
            NormalizedCashRow(
                source_row_number=source_row_number,
                entry_date=entry_date,
                amount=amount,
                movement_type=movement_type,
                description=compose_description(
                    get_row_value(row, tiers_idx),
                    get_row_value(row, libelle_idx),
                )
                or "Import Excel",
            )
        )

    return parsed_sheet, rows, issues, ignored_issues


def parse_bank_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedBankRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    """Parse bank rows into a shared normalized structure."""
    header_info = detect_header_row(ws, ["date", "debit"])
    if header_info is None:
        header_info = detect_header_row(ws, ["date", "credit"])
    if header_info is None:
        header_info = detect_header_row(ws, ["date", "montant"])
    if header_info is None:
        return None, [], [], []

    header_row, col_map = header_info
    date_idx = find_col_idx(col_map, "date")
    debit_idx = find_col_idx(col_map, "débit", "debit")
    credit_idx = find_col_idx(col_map, "crédit", "credit")
    montant_idx = (
        find_col_idx(col_map, "montant") if debit_idx is None and credit_idx is None else None
    )
    libelle_idx = find_col_idx(col_map, "libel", "descr", "label", "intitul")
    solde_idx = find_col_idx(col_map, "solde", "balance")

    missing_columns = bank_missing_columns(
        date_idx=date_idx,
        debit_idx=debit_idx,
        credit_idx=credit_idx,
        montant_idx=montant_idx,
    )

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, [], [], []

    rows: list[NormalizedBankRow] = []
    issues: list[RowValidationIssue] = []
    ignored_issues: list[RowIgnoredIssue] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        amount: Decimal | None = None
        if debit_idx is not None or credit_idx is not None:
            debit = parse_decimal(get_row_value(row, debit_idx)) or Decimal("0")
            credit = parse_decimal(get_row_value(row, credit_idx)) or Decimal("0")
            if credit > 0:
                amount = credit
            elif debit > 0:
                amount = -debit
        elif montant_idx is not None:
            amount = parse_decimal(get_row_value(row, montant_idx))

        entry_date = parse_date(get_row_value(row, date_idx))
        if entry_date is None:
            if should_ignore_bank_balance_description(
                entry_date=entry_date,
                amount=amount,
                label=parse_str(get_row_value(row, libelle_idx)),
                balance=parse_decimal(get_row_value(row, solde_idx)),
            ):
                ignored_issues.append(
                    RowIgnoredIssue(
                        source_row_number=source_row_number,
                        message=BANK_BALANCE_DESCRIPTION_MESSAGE,
                    )
                )
                continue
            issues.append(make_validation_issue(source_row_number, [BANK_INVALID_DATE_MESSAGE]))
            continue

        if amount is None or amount == 0:
            issues.append(make_validation_issue(source_row_number, [BANK_INVALID_AMOUNT_MESSAGE]))
            continue

        rows.append(
            NormalizedBankRow(
                source_row_number=source_row_number,
                entry_date=entry_date,
                amount=amount,
                description=parse_str(get_row_value(row, libelle_idx), max_len=500)
                or "Import Excel",
                balance_after=parse_decimal(get_row_value(row, solde_idx)) or Decimal("0"),
            )
        )

    return parsed_sheet, rows, issues, ignored_issues


def parse_entries_sheet(
    ws: Any,
) -> tuple[
    ParsedSheet | None,
    list[NormalizedEntryRow],
    list[RowValidationIssue],
    list[RowIgnoredIssue],
]:
    """Parse accounting journal rows into a shared normalized structure."""
    header_info = detect_header_row(ws, ["compte", "débit"])
    if header_info is None:
        header_info = detect_header_row(ws, ["compte", "credit"])
    if header_info is None:
        return None, [], [], []

    header_row, col_map = header_info
    date_idx = find_col_idx(col_map, "date")
    compte_idx = find_col_idx(col_map, "compte")
    libelle_idx = find_col_idx(col_map, "libel", "label")
    debit_idx = find_col_idx(col_map, "débit", "debit")
    credit_idx = find_col_idx(col_map, "crédit", "credit")

    missing_columns = entries_missing_columns(
        compte_idx=compte_idx,
        debit_idx=debit_idx,
        credit_idx=credit_idx,
    )

    parsed_sheet = ParsedSheet(
        header_row=header_row,
        col_map=col_map,
        missing_columns=missing_columns,
    )
    if missing_columns:
        return parsed_sheet, [], [], []

    rows: list[NormalizedEntryRow] = []
    issues: list[RowValidationIssue] = []
    ignored_issues: list[RowIgnoredIssue] = []
    for source_row_number, row in enumerate(
        ws.iter_rows(min_row=header_row + 1, values_only=True),
        start=header_row + 1,
    ):
        if all(cell is None for cell in row):
            continue

        raw_date = get_row_value(row, date_idx)
        entry_date = parse_date(raw_date)
        account_number = parse_str(get_row_value(row, compte_idx), max_len=20)
        raw_debit = get_row_value(row, debit_idx)
        raw_credit = get_row_value(row, credit_idx)
        debit = parse_decimal(raw_debit)
        credit = parse_decimal(raw_credit)

        row_errors: list[str] = []
        if raw_date not in (None, "") and entry_date is None:
            row_errors.append(ENTRY_INVALID_DATE_MESSAGE)
        if not account_number:
            row_errors.append(ENTRY_MISSING_ACCOUNT_MESSAGE)
        if raw_debit not in (None, "") and debit is None:
            row_errors.append(ENTRY_INVALID_DEBIT_MESSAGE)
        if raw_credit not in (None, "") and credit is None:
            row_errors.append(ENTRY_INVALID_CREDIT_MESSAGE)

        debit_value = debit or Decimal("0")
        credit_value = credit or Decimal("0")
        if row_errors:
            issues.append(make_validation_issue(source_row_number, row_errors))
            continue

        if should_ignore_zero_journal_entry(debit=debit_value, credit=credit_value):
            ignored_issues.append(
                RowIgnoredIssue(
                    source_row_number=source_row_number,
                    message=ZERO_JOURNAL_ENTRY_MESSAGE,
                )
            )
            continue

        rows.append(
            NormalizedEntryRow(
                source_row_number=source_row_number,
                entry_date=entry_date or date.today(),
                account_number=account_number,
                label=parse_str(get_row_value(row, libelle_idx), max_len=500) or "Import Excel",
                debit=debit_value,
                credit=credit_value,
            )
        )

    return parsed_sheet, rows, issues, ignored_issues
