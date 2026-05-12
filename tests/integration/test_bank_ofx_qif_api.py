"""Integration tests for bank OFX/QIF import endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank import BankAccountType, BankTransaction, BankTransactionSource

_OFX_CONTENT = """\
<?xml version="1.0" encoding="UTF-8"?>
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <DTPOSTED>20250415</DTPOSTED>
            <TRNAMT>-100.00</TRNAMT>
            <NAME>TEST OFX</NAME>
            <FITID>TX001</FITID>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""

_QIF_CONTENT = """\
!Type:Bank
D15/04/2025
T-100.00
PTEST QIF
NTX001
^
"""


@pytest.mark.asyncio
async def test_import_ofx_success(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/bank/transactions/import-ofx",
        json={"content": _OFX_CONTENT},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["skipped"] == 0
    assert len(data["created"]) == 1
    assert data["created"][0]["amount"] == "-100.00"
    assert data["created"][0]["description"] == "TEST OFX"
    assert data["created"][0]["detected_category"] == "other_debit"


@pytest.mark.asyncio
async def test_import_ofx_invalid_content(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/bank/transactions/import-ofx",
        json={"content": "<OFX></OFX>"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_import_qif_success(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/bank/transactions/import-qif",
        json={"content": _QIF_CONTENT},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["skipped"] == 0
    assert len(data["created"]) == 1
    assert data["created"][0]["amount"] == "-100.00"
    assert data["created"][0]["description"] == "TEST QIF"
    assert data["created"][0]["detected_category"] == "other_debit"


@pytest.mark.asyncio
async def test_import_qif_invalid_content(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/bank/transactions/import-qif",
        json={"content": "!Type:Bank\n"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_import_ofx_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/bank/transactions/import-ofx",
        json={"content": _OFX_CONTENT},
    )
    assert response.status_code == 401


_OFX_MULTI_ACCOUNT = """\
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKACCTFROM><ACCTID>FR001</ACCTID></BANKACCTFROM>
        <BANKTRANLIST>
          <STMTTRN>
            <DTPOSTED>20250415</DTPOSTED>
            <TRNAMT>-100.00</TRNAMT>
            <NAME>TEST COMPTE A</NAME>
            <FITID>TXMA001</FITID>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
    <STMTTRNRS>
      <STMTRS>
        <BANKACCTFROM><ACCTID>FR002</ACCTID></BANKACCTFROM>
        <BANKTRANLIST>
          <STMTTRN>
            <DTPOSTED>20250416</DTPOSTED>
            <TRNAMT>200.00</TRNAMT>
            <NAME>TEST COMPTE B</NAME>
            <FITID>TXMA002</FITID>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""


@pytest.mark.asyncio
async def test_import_ofx_multi_account_returns_422(
    client: AsyncClient, auth_headers: dict
) -> None:
    """OFX with multiple STMTTRNRS blocks must be rejected with a clear 422 error."""
    response = await client.post(
        "/api/bank/transactions/import-ofx",
        json={"content": _OFX_MULTI_ACCOUNT},
        headers=auth_headers,
    )
    assert response.status_code == 422
    detail = response.json()["detail"]["detail"]
    assert "2 comptes" in detail
    assert "FR001" in detail
    assert "FR002" in detail


@pytest.mark.asyncio
async def test_import_ofx_dedup_skips_existing(client: AsyncClient, auth_headers: dict) -> None:
    """Importing the same OFX file twice must skip already-present transactions."""
    # First import — all rows created
    r1 = await client.post(
        "/api/bank/transactions/import-ofx",
        json={"content": _OFX_CONTENT},
        headers=auth_headers,
    )
    assert r1.status_code == 201
    assert r1.json()["skipped"] == 0
    assert len(r1.json()["created"]) == 1

    # Second import — same FITID already in DB, must be skipped
    r2 = await client.post(
        "/api/bank/transactions/import-ofx",
        json={"content": _OFX_CONTENT},
        headers=auth_headers,
    )
    assert r2.status_code == 201
    assert r2.json()["skipped"] == 1
    assert r2.json()["created"] == []


@pytest.mark.asyncio
async def test_ofx_import_respects_excel_cutoff(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """OFX rows on or before the latest Excel-imported transaction date must be skipped."""
    from datetime import date
    from decimal import Decimal

    # Simulate a prior Excel import with a transaction on 2025-04-15
    excel_tx = BankTransaction(
        date=date(2025, 4, 15),
        amount=Decimal("-50.00"),
        balance_after=Decimal("1000.00"),
        description="EXCEL IMPORT",
        reference=None,
        source=BankTransactionSource.IMPORT_EXCEL,
        bank_account=BankAccountType.COURANT,
        reconciled=False,
    )
    db_session.add(excel_tx)
    await db_session.commit()

    # OFX with two transactions: one on 2025-04-15 (≤ cutoff → skipped) and one on
    # 2025-04-20 (> cutoff → imported)
    ofx = """\
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <DTPOSTED>20250415</DTPOSTED>
            <TRNAMT>-100.00</TRNAMT>
            <NAME>OLD TX</NAME>
            <FITID>CUTOFF001</FITID>
          </STMTTRN>
          <STMTTRN>
            <DTPOSTED>20250420</DTPOSTED>
            <TRNAMT>-200.00</TRNAMT>
            <NAME>NEW TX</NAME>
            <FITID>CUTOFF002</FITID>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""

    response = await client.post(
        "/api/bank/transactions/import-ofx",
        json={"content": ofx},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["skipped"] == 1  # 2025-04-15 blocked by cut-off
    assert len(data["created"]) == 1  # only 2025-04-20 imported
    assert data["created"][0]["description"] == "NEW TX"
