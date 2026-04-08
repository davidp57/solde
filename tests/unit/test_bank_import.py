"""Unit tests for the CSV import service (bank_import)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from backend.services.bank_import import BankImportError, parse_credit_mutuel_csv

_VALID_CSV = """\
Date;Valeur;Montant;Libellé;Solde
01/03/2024;01/03/2024;150,00;VIR ALICE MARTIN;1 650,00
05/03/2024;05/03/2024;-45,50;PRELEVEMENT EDF;1 604,50
"""


def test_parse_valid_csv() -> None:
    rows = parse_credit_mutuel_csv(_VALID_CSV)
    assert len(rows) == 2


def test_parse_first_row_date() -> None:
    rows = parse_credit_mutuel_csv(_VALID_CSV)
    assert rows[0]["date"] == date(2024, 3, 1)


def test_parse_first_row_amount() -> None:
    rows = parse_credit_mutuel_csv(_VALID_CSV)
    assert rows[0]["amount"] == Decimal("150.00")


def test_parse_second_row_negative_amount() -> None:
    rows = parse_credit_mutuel_csv(_VALID_CSV)
    assert rows[1]["amount"] == Decimal("-45.50")


def test_parse_description() -> None:
    rows = parse_credit_mutuel_csv(_VALID_CSV)
    assert rows[0]["description"] == "VIR ALICE MARTIN"


def test_parse_balance_after() -> None:
    rows = parse_credit_mutuel_csv(_VALID_CSV)
    assert rows[0]["balance_after"] == Decimal("1650.00")


def test_parse_empty_file_raises() -> None:
    with pytest.raises(BankImportError):
        parse_credit_mutuel_csv("Date;Valeur;Montant;Libellé;Solde\n")


def test_parse_invalid_date_raises() -> None:
    bad = "Date;Valeur;Montant;Libellé;Solde\nNOT-A-DATE;...;100,00;Desc;100,00\n"
    with pytest.raises(BankImportError, match="invalid date"):
        parse_credit_mutuel_csv(bad)


def test_parse_invalid_amount_raises() -> None:
    bad = "Date;Valeur;Montant;Libellé;Solde\n01/01/2024;01/01/2024;NOT_AMOUNT;Desc;100,00\n"
    with pytest.raises(BankImportError, match="invalid amount"):
        parse_credit_mutuel_csv(bad)


def test_parse_with_narrow_no_break_space() -> None:
    """French locale uses narrow no-break space (U+202F) as thousands separator."""
    csv = (
        "Date;Valeur;Montant;Libellé;Solde\n"
        "10/01/2024;10/01/2024;1\u202f234,56;Desc;1\u202f234,56\n"
    )
    rows = parse_credit_mutuel_csv(csv)
    assert rows[0]["amount"] == Decimal("1234.56")
