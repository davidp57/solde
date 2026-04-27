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
    split_contact_full_name,
)
from backend.services.excel_import_policy import (
    BANK_BALANCE_DESCRIPTION_MESSAGE,
    BANK_INVALID_AMOUNT_MESSAGE,
    BANK_INVALID_DATE_MESSAGE,
    BANK_SUSPICIOUS_DATE_MESSAGE,
    CASH_INITIAL_BALANCE_MESSAGE,
    CASH_INVALID_DATE_MESSAGE,
    CASH_INVALID_MOVEMENT_MESSAGE,
    CASH_PENDING_DEPOSIT_MESSAGE,
    CASH_SUSPICIOUS_DATE_MESSAGE,
    CONTACT_REQUIRED_NAME_MESSAGE,
    ENTRY_INVALID_CREDIT_MESSAGE,
    ENTRY_INVALID_DATE_MESSAGE,
    ENTRY_INVALID_DEBIT_MESSAGE,
    ENTRY_MISSING_ACCOUNT_MESSAGE,
    ENTRY_SUSPICIOUS_DATE_MESSAGE,
    INVOICE_INVALID_AMOUNT_MESSAGE,
    INVOICE_INVALID_COMPONENT_BREAKDOWN_MESSAGE,
    INVOICE_INVALID_DATE_MESSAGE,
    INVOICE_REQUIRED_CONTACT_MESSAGE,
    INVOICE_TOTAL_MESSAGE,
    PAYMENT_INVALID_AMOUNT_MESSAGE,
    PAYMENT_REQUIRED_REFERENCE_OR_CONTACT_MESSAGE,
    PAYMENT_SUSPICIOUS_DATE_MESSAGE,
    SALARY_INVALID_AMOUNT_MESSAGE,
    SALARY_INVALID_MONTH_MESSAGE,
    SALARY_REQUIRED_EMPLOYEE_MESSAGE,
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
    NormalizedSalaryRow,
    ParsedSheet,
    RowIgnoredIssue,
    RowValidationIssue,
)

_DATE_LIKE_TEXT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$|^\d{2}/\d{2}/\d{4}$|^\d{2}-\d{2}-\d{4}$"
)
_SALARY_MONTH_RE = re.compile(r"^(20\d{2})\.(\d{2})$")
_BANK_NEIGHBOR_DATE_WINDOW_DAYS = 31
_BANK_ISOLATED_DATE_GAP_DAYS = 180


def _filter_rows_with_suspicious_dates(
    rows: list[Any],
    issues: list[RowValidationIssue],
    *,
    get_date: Any,
    get_source_row_number: Any,
    message: str,
) -> list[Any]:
    suspicious_indexes: set[int] = set()
    index = 1
    while index < len(rows) - 1:
        previous_date = get_date(rows[index - 1])
        suspicious_end_index: int | None = None
        for boundary_index in range(index + 1, len(rows)):
            boundary_date = get_date(rows[boundary_index])
            if abs((boundary_date - previous_date).days) > _BANK_NEIGHBOR_DATE_WINDOW_DAYS:
                continue
            if all(
                abs((get_date(rows[candidate_index]) - previous_date).days)
                >= _BANK_ISOLATED_DATE_GAP_DAYS
                and abs((get_date(rows[candidate_index]) - boundary_date).days)
                >= _BANK_ISOLATED_DATE_GAP_DAYS
                for candidate_index in range(index, boundary_index)
            ):
                suspicious_end_index = boundary_index
                break

        if suspicious_end_index is None:
            index += 1
            continue
        for suspicious_index in range(index, suspicious_end_index):
            suspicious_indexes.add(suspicious_index)
            issues.append(
                make_validation_issue(
                    get_source_row_number(rows[suspicious_index]),
                    [message],
                )
            )
        index = suspicious_end_index

    if not suspicious_indexes:
        return rows

    return [row for index, row in enumerate(rows) if index not in suspicious_indexes]


def _parse_salary_month(value: Any) -> str | None:
    text = parse_str(value)
    if not text:
        return None
    match = _SALARY_MONTH_RE.match(text)
    if match is None:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def _has_explicit_component_value(value: Any) -> bool:
    return parse_str(value) != ""


def _salary_decimal_or_zero(value: Any) -> Decimal:
    return parse_decimal(value) or Decimal("0")


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
    course_amount_idx = find_col_idx(col_map, "montant cours", "cours")
    adhesion_amount_idx = find_col_idx(
        col_map,
        "montant adhésion",
        "montant adhesion",
        "adhésion",
        "adhesion",
    )

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
        normalized_label = normalize_invoice_label(get_row_value(row, label_idx))
        invoice_number: str | None = None
        if not isinstance(raw_number, (date, datetime)):
            candidate = parse_str(raw_number)
            if candidate and not _DATE_LIKE_TEXT_RE.match(candidate):
                invoice_number = candidate

        raw_course_amount = get_row_value(row, course_amount_idx)
        raw_adhesion_amount = get_row_value(row, adhesion_amount_idx)
        course_amount = parse_decimal(raw_course_amount)
        adhesion_amount = parse_decimal(raw_adhesion_amount)
        if normalized_label == "cs+a":
            has_explicit_breakdown = _has_explicit_component_value(
                raw_course_amount
            ) or _has_explicit_component_value(raw_adhesion_amount)
            if has_explicit_breakdown:
                valid_course_amount = (
                    course_amount if course_amount is not None and course_amount >= 0 else None
                )
                valid_adhesion_amount = (
                    adhesion_amount
                    if adhesion_amount is not None and adhesion_amount >= 0
                    else None
                )
                component_total = (valid_course_amount or Decimal("0")) + (
                    valid_adhesion_amount or Decimal("0")
                )
                if (
                    valid_course_amount is None
                    or valid_adhesion_amount is None
                    or component_total != amount
                ):
                    issues.append(
                        make_validation_issue(
                            source_row_number,
                            [INVOICE_INVALID_COMPONENT_BREAKDOWN_MESSAGE],
                        )
                    )
                    continue
                course_amount = valid_course_amount
                adhesion_amount = valid_adhesion_amount
            else:
                course_amount = None
                adhesion_amount = None
        else:
            course_amount = None
            adhesion_amount = None

        rows.append(
            NormalizedInvoiceRow(
                source_row_number=source_row_number,
                invoice_date=invoice_date,
                amount=amount,
                contact_name=contact_name,
                invoice_number=invoice_number,
                label=normalized_label,
                course_amount=course_amount,
                adhesion_amount=adhesion_amount,
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
    # Resolve deposit_date_idx first: "date encaissement" must not bleed into deposited_idx
    # because "encaisse" is a substring of "date encaissement".
    deposit_date_idx = find_col_idx(col_map, "date encaissement")
    deposited_idx = find_col_idx(col_map, "encaissé", "encaisse")
    if deposited_idx is not None and deposited_idx == deposit_date_idx:
        # Substring match grabbed the wrong column — fall back to exact key lookup
        deposited_idx = col_map.get("encaisse")

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

    rows = _filter_rows_with_suspicious_dates(
        rows,
        issues,
        get_date=lambda row: row.payment_date,
        get_source_row_number=lambda row: row.source_row_number,
        message=PAYMENT_SUSPICIOUS_DATE_MESSAGE,
    )

    return parsed_sheet, rows, issues


def parse_salary_sheet(
    ws: Any,
) -> tuple[ParsedSheet | None, list[NormalizedSalaryRow], list[RowValidationIssue]]:
    """Parse historical `Aide Salaires` rows into salary records."""
    parsed_sheet = ParsedSheet(
        header_row=1,
        col_map={
            "month": 0,
            "employee": 0,
            "hours": 1,
            "gross": 2,
            "employee_charges": 3,
            "employer_charges": 4,
            "tax": 5,
            "net": 6,
        },
        missing_columns=[],
    )

    rows: list[NormalizedSalaryRow] = []
    issues: list[RowValidationIssue] = []
    current_month: str | None = None
    current_format: str | None = None

    for source_row_number, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if all(cell is None for cell in row):
            continue

        first_cell = parse_str(get_row_value(row, 0))
        parsed_month = _parse_salary_month(first_cell)
        if parsed_month is not None:
            current_month = parsed_month
            if normalize_text(parse_str(get_row_value(row, 1))) == "heures":
                current_format = "detailed"
            else:
                current_format = None
            continue

        if normalize_text(first_cell) == "nom":
            current_format = "compact"
            continue

        if current_month is None or current_format is None or not first_cell:
            continue

        normalized_name = normalize_text(first_cell)
        if normalized_name in {"total", "total charges fixes"}:
            continue

        if current_format == "detailed":
            hours = _salary_decimal_or_zero(get_row_value(row, 1))
            _brut_declared_raw = _salary_decimal_or_zero(get_row_value(row, 2))
            _conges_raw = _salary_decimal_or_zero(get_row_value(row, 3))
            _precarite_raw = _salary_decimal_or_zero(get_row_value(row, 4))
            gross = _salary_decimal_or_zero(get_row_value(row, 6))
            employee_charges = _salary_decimal_or_zero(get_row_value(row, 7))
            employer_charges = _salary_decimal_or_zero(get_row_value(row, 8))
            tax = _salary_decimal_or_zero(get_row_value(row, 9))
            net_pay = _salary_decimal_or_zero(get_row_value(row, 10))
            # Store CDD breakdown only when CP or précarité are non-zero (CDI rows have 0)
            if _conges_raw > 0 or _precarite_raw > 0:
                brut_declared: Decimal | None = _brut_declared_raw
                conges_payes: Decimal | None = _conges_raw
                precarite: Decimal | None = _precarite_raw
            else:
                brut_declared = None
                conges_payes = None
                precarite = None
        else:
            hours = _salary_decimal_or_zero(get_row_value(row, 1))
            gross = _salary_decimal_or_zero(get_row_value(row, 2))
            employee_charges = _salary_decimal_or_zero(get_row_value(row, 3))
            employer_charges = _salary_decimal_or_zero(get_row_value(row, 4))
            tax = _salary_decimal_or_zero(get_row_value(row, 5))
            net_pay = _salary_decimal_or_zero(get_row_value(row, 6))
            brut_declared = None
            conges_payes = None
            precarite = None

        row_errors: list[str] = []
        if not first_cell:
            row_errors.append(SALARY_REQUIRED_EMPLOYEE_MESSAGE)
        if current_month is None:
            row_errors.append(SALARY_INVALID_MONTH_MESSAGE)
        if gross <= 0 and net_pay <= 0 and employee_charges <= 0 and employer_charges <= 0:
            continue
        if gross <= 0 or net_pay < 0 or employee_charges < 0 or employer_charges < 0 or tax < 0:
            row_errors.append(SALARY_INVALID_AMOUNT_MESSAGE)

        if row_errors:
            issues.append(make_validation_issue(source_row_number, row_errors))
            continue

        rows.append(
            NormalizedSalaryRow(
                source_row_number=source_row_number,
                month=current_month,
                employee_name=first_cell,
                hours=hours,
                gross=gross,
                employee_charges=employee_charges,
                employer_charges=employer_charges,
                tax=tax,
                net_pay=net_pay,
                brut_declared=brut_declared,
                conges_payes=conges_payes,
                precarite=precarite,
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
        nom, prenom = split_contact_full_name(nom, prenom)
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
                reference=parse_str(get_row_value(row, libelle_idx)) or None,
                contact_name=parse_str(get_row_value(row, tiers_idx)) or None,
                description=compose_description(
                    get_row_value(row, tiers_idx),
                    get_row_value(row, libelle_idx),
                )
                or "Import Excel",
            )
        )

    rows = _filter_rows_with_suspicious_dates(
        rows,
        issues,
        get_date=lambda row: row.entry_date,
        get_source_row_number=lambda row: row.source_row_number,
        message=CASH_SUSPICIOUS_DATE_MESSAGE,
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
    reference_idx = find_col_idx(col_map, "référence", "reference", "réf", "ref")
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

        if entry_date is None:
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
                reference=parse_str(get_row_value(row, reference_idx)) or None,
                description=parse_str(get_row_value(row, libelle_idx), max_len=500)
                or "Import Excel",
                balance_after=parse_decimal(get_row_value(row, solde_idx)) or Decimal("0"),
            )
        )

    rows = _filter_rows_with_suspicious_dates(
        rows,
        issues,
        get_date=lambda row: row.entry_date,
        get_source_row_number=lambda row: row.source_row_number,
        message=BANK_SUSPICIOUS_DATE_MESSAGE,
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
    change_idx = find_col_idx(col_map, "changenum", "change num")

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
                change_marker=parse_str(get_row_value(row, change_idx), max_len=20) or None,
            )
        )

    rows = _filter_rows_with_suspicious_dates(
        rows,
        issues,
        get_date=lambda row: row.entry_date,
        get_source_row_number=lambda row: row.source_row_number,
        message=ENTRY_SUSPICIOUS_DATE_MESSAGE,
    )

    return parsed_sheet, rows, issues, ignored_issues
