"""Integration tests for bank OFX/QIF import endpoints."""

import pytest
from httpx import AsyncClient

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
    assert len(data) == 1
    assert data[0]["amount"] == "-100.00"
    assert data[0]["description"] == "TEST OFX"
    assert data[0]["detected_category"] == "other_debit"


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
    assert len(data) == 1
    assert data[0]["amount"] == "-100.00"
    assert data[0]["description"] == "TEST QIF"
    assert data[0]["detected_category"] == "other_debit"


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
