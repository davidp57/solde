"""Unit tests for the CSV, OFX and QIF import service (bank_import)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from backend.models.bank import BankTransactionCategory
from backend.services.bank_import import (
    BankImportError,
    detect_transaction_category,
    parse_credit_mutuel_csv,
    parse_ofx,
    parse_qif,
)

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


# ---------------------------------------------------------------------------
# OFX / QFX
# ---------------------------------------------------------------------------

_OFX_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <DTPOSTED>20250415120000</DTPOSTED>
            <TRNAMT>-150.00</TRNAMT>
            <NAME>VIREMENT EDF</NAME>
            <MEMO>Facture mars</MEMO>
            <FITID>20250415001</FITID>
          </STMTTRN>
          <STMTTRN>
            <DTPOSTED>20250416</DTPOSTED>
            <TRNAMT>500.00</TRNAMT>
            <NAME>ADHESION</NAME>
            <FITID>20250416001</FITID>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""


def test_ofx_xml_two_transactions() -> None:
    rows = parse_ofx(_OFX_XML)
    assert len(rows) == 2


def test_ofx_xml_negative_amount() -> None:
    rows = parse_ofx(_OFX_XML)
    assert rows[0]["amount"] == Decimal("-150.00")


def test_ofx_xml_positive_amount() -> None:
    rows = parse_ofx(_OFX_XML)
    assert rows[1]["amount"] == Decimal("500.00")


def test_ofx_xml_dates() -> None:
    rows = parse_ofx(_OFX_XML)
    assert rows[0]["date"] == date(2025, 4, 15)
    assert rows[1]["date"] == date(2025, 4, 16)


def test_ofx_xml_description_merges_memo() -> None:
    rows = parse_ofx(_OFX_XML)
    desc = str(rows[0]["description"])
    assert "VIREMENT EDF" in desc
    assert "Facture mars" in desc


def test_ofx_xml_reference() -> None:
    rows = parse_ofx(_OFX_XML)
    assert rows[0]["reference"] == "20250415001"


def test_ofx_empty_raises() -> None:
    with pytest.raises(BankImportError):
        parse_ofx("<OFX></OFX>")


def test_detect_customer_payment_category() -> None:
    category = detect_transaction_category(
        amount=Decimal("52.00"),
        description="VIR INST ANNE WENTZO VIREMENT DE",
    )
    assert category == BankTransactionCategory.CUSTOMER_PAYMENT


def test_detect_cheque_deposit_category() -> None:
    category = detect_transaction_category(
        amount=Decimal("388.00"),
        description="REM CHQ REF05001A05",
    )
    assert category == BankTransactionCategory.CHEQUE_DEPOSIT


def test_detect_cash_deposit_category() -> None:
    category = detect_transaction_category(
        amount=Decimal("700.00"),
        description="VRST REF05001A05",
    )
    assert category == BankTransactionCategory.CASH_DEPOSIT


def test_detect_salary_category() -> None:
    category = detect_transaction_category(
        amount=Decimal("-1249.64"),
        description="VIR INST SALAIRE LAY 2026.02 VG6",
    )
    assert category == BankTransactionCategory.SALARY


def test_detect_social_charge_category() -> None:
    category = detect_transaction_category(
        amount=Decimal("-800.00"),
        description="PRLV SEPA URSSAF DE LORRAINE TT4",
    )
    assert category == BankTransactionCategory.SOCIAL_CHARGE


# ---------------------------------------------------------------------------
# QIF
# ---------------------------------------------------------------------------

_QIF_CONTENT = """\
!Type:Bank
D15/04/2025
T-150.00
PVIREMENT EDF
NTX001
^
D16/04/2025
T500.00
PADHESION
^
"""


def test_qif_two_transactions() -> None:
    rows = parse_qif(_QIF_CONTENT)
    assert len(rows) == 2


def test_qif_negative_amount() -> None:
    rows = parse_qif(_QIF_CONTENT)
    assert rows[0]["amount"] == Decimal("-150.00")


def test_qif_positive_amount() -> None:
    rows = parse_qif(_QIF_CONTENT)
    assert rows[1]["amount"] == Decimal("500.00")


def test_qif_date_dd_mm_yyyy() -> None:
    rows = parse_qif(_QIF_CONTENT)
    assert rows[0]["date"] == date(2025, 4, 15)


def test_qif_date_dd_mm_yy() -> None:
    qif = "!Type:Bank\nD15/04/25\nT-75.50\nPLOYER\n^\n"
    rows = parse_qif(qif)
    assert rows[0]["date"] == date(2025, 4, 15)


def test_qif_description_and_reference() -> None:
    rows = parse_qif(_QIF_CONTENT)
    assert rows[0]["description"] == "VIREMENT EDF"
    assert rows[0]["reference"] == "TX001"


def test_qif_last_record_without_terminator() -> None:
    qif = "!Type:Bank\nD01/03/2025\nT200.00\nPDON\n"
    rows = parse_qif(qif)
    assert len(rows) == 1
    assert rows[0]["amount"] == Decimal("200.00")


def test_qif_empty_raises() -> None:
    with pytest.raises(BankImportError):
        parse_qif("!Type:Bank\n")
