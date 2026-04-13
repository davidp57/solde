"""CSV, OFX and QIF import service for bank statements."""

from __future__ import annotations

import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation


class BankImportError(ValueError):
    """Raised when a bank statement file cannot be parsed."""


def parse_credit_mutuel_csv(content: str) -> list[dict[str, object]]:
    """Parse a Crédit Mutuel CSV export and return a list of transaction dicts.

    Expected columns (semicolon-separated):
        Date;Valeur;Montant;Libellé;Solde
    Returns a list of dicts with keys:
        date, amount, balance_after, description, reference (empty)
    """
    rows: list[dict[str, object]] = []

    reader = csv.reader(io.StringIO(content.strip()), delimiter=";")
    headers: list[str] | None = None

    for line_no, row in enumerate(reader, start=1):
        if not row or all(cell.strip() == "" for cell in row):
            continue

        if headers is None:
            headers = [h.strip().lower() for h in row]
            continue

        if len(row) < len(headers):
            raise BankImportError(
                f"line {line_no}: expected {len(headers)} columns, got {len(row)}"
            )

        record = dict(zip(headers, [cell.strip() for cell in row], strict=False))

        # Parse date (DD/MM/YYYY)
        raw_date = record.get("date", "")
        try:
            day, month, year = str(raw_date).split("/")
            tx_date = date(int(year), int(month), int(day))
        except (ValueError, KeyError) as exc:
            raise BankImportError(f"line {line_no}: invalid date '{raw_date}'") from exc

        # Parse amount (French locale: "1 234,56" or "-1 234,56")
        raw_amount = record.get("montant", "")
        try:
            normalised = str(raw_amount).replace("\u202f", "").replace(" ", "").replace(",", ".")
            amount = Decimal(normalised)
        except InvalidOperation as exc:
            raise BankImportError(f"line {line_no}: invalid amount '{raw_amount}'") from exc

        # Parse balance (may be absent)
        raw_balance = record.get("solde", "0")
        try:
            norm_bal = str(raw_balance).replace("\u202f", "").replace(" ", "").replace(",", ".")
            balance_after = Decimal(norm_bal) if norm_bal else Decimal("0")
        except InvalidOperation:
            balance_after = Decimal("0")

        description = record.get("libellé", record.get("libelle", ""))

        rows.append(
            {
                "date": tx_date,
                "amount": amount,
                "balance_after": balance_after,
                "description": str(description),
                "reference": None,
            }
        )

    if not rows:
        raise BankImportError("no transactions found in file")

    return rows


# ---------------------------------------------------------------------------
# OFX / QFX (Open Financial Exchange)
# ---------------------------------------------------------------------------


def parse_ofx(content: str) -> list[dict[str, object]]:
    """Parse an OFX/QFX bank statement (SGML or XML) and return transaction dicts.

    Returns a list of dicts with keys:
        date, amount, balance_after, description, reference
    """
    rows: list[dict[str, object]] = []

    # Extract STMTTRN blocks (works for both SGML and XML OFX)
    blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", content, re.DOTALL | re.IGNORECASE)
    if not blocks:
        # SGML OFX without closing tags: split on <STMTTRN>
        raw_blocks = re.split(r"<STMTTRN>", content, flags=re.IGNORECASE)[1:]
        # Each block ends at <BANKTRANLIST end> or next <STMTTRN> or </BANKTRANLIST>
        blocks = [re.split(r"</BANKTRANLIST>|<STMTTRN>", b, maxsplit=1)[0] for b in raw_blocks]

    for idx, block in enumerate(blocks, start=1):

        def _get(tag: str, _block: str = block) -> str | None:
            m = re.search(rf"<{tag}>([^\n<]*)", _block, re.IGNORECASE)
            return m.group(1).strip() if m else None

        dtposted = _get("DTPOSTED")
        trnamt = _get("TRNAMT")
        if not dtposted or not trnamt:
            continue

        # Parse date: YYYYMMDDHHMMSS[.mmm][±hh:mm] → take first 8 chars
        date_str = re.sub(r"[^\d].*$", "", dtposted)[:8]
        if len(date_str) < 8:
            raise BankImportError(f"OFX record {idx}: invalid date '{dtposted}'")
        try:
            tx_date = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
        except ValueError as exc:
            raise BankImportError(f"OFX record {idx}: invalid date '{dtposted}'") from exc

        # Parse amount (always dot-separated in OFX standard)
        try:
            amount = Decimal(trnamt.replace(",", "."))
        except InvalidOperation as exc:
            raise BankImportError(f"OFX record {idx}: invalid amount '{trnamt}'") from exc

        name = _get("NAME") or ""
        memo = _get("MEMO") or ""
        description = name
        if memo and memo != name:
            description = f"{description} {memo}".strip()
        reference = _get("FITID")

        rows.append(
            {
                "date": tx_date,
                "amount": amount,
                "balance_after": Decimal("0"),
                "description": description,
                "reference": reference,
            }
        )

    if not rows:
        raise BankImportError("no transactions found in OFX file")
    return rows


# ---------------------------------------------------------------------------
# QIF (Quicken Interchange Format)
# ---------------------------------------------------------------------------


def _parse_qif_date(raw: str, record_no: int) -> date:
    """Try multiple QIF date formats: DD/MM/YYYY, MM/DD/YYYY, DD/MM/YY, YYYY-MM-DD."""
    raw = raw.strip().replace("-", "/").replace("'", "/")
    parts = raw.split("/")
    if len(parts) == 3:
        a, b, c = parts
        # Guess year field
        if len(c) == 4:
            year = int(c)
            # Prefer DD/MM/YYYY (French banks)
            try:
                return date(year, int(b), int(a))
            except ValueError:
                pass
            # Fall back to MM/DD/YYYY (US)
            try:
                return date(year, int(a), int(b))
            except ValueError:
                pass
        elif len(c) == 2:
            year = 2000 + int(c) if int(c) <= 50 else 1900 + int(c)
            try:
                return date(year, int(b), int(a))
            except ValueError:
                pass
    raise BankImportError(f"QIF record {record_no}: cannot parse date '{raw}'")


def _parse_qif_amount(raw: str, record_no: int) -> Decimal:
    """Parse QIF amount — handles '1,234.56', '1 234,56', '-1234.56'."""
    raw = raw.strip()
    # Detect French locale (dot as thousands separator, comma as decimal)
    if re.search(r"\d\.\d{3}(,|$)", raw):
        raw = raw.replace(".", "").replace(",", ".")
    else:
        # US/standard: comma is thousands separator
        raw = raw.replace(",", "")
    raw = raw.replace(" ", "")
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise BankImportError(f"QIF record {record_no}: invalid amount '{raw}'") from exc


def parse_qif(content: str) -> list[dict[str, object]]:
    """Parse a QIF bank statement and return transaction dicts.

    Returns a list of dicts with keys:
        date, amount, balance_after, description, reference
    """
    rows: list[dict[str, object]] = []
    record: dict[str, str] = {}
    record_no = 0

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("!"):
            continue

        if line == "^":
            if "date" in record and "amount" in record:
                record_no += 1
                rows.append(
                    {
                        "date": _parse_qif_date(record["date"], record_no),
                        "amount": _parse_qif_amount(record["amount"], record_no),
                        "balance_after": Decimal("0"),
                        "description": record.get("description", ""),
                        "reference": record.get("reference"),
                    }
                )
            record = {}
            continue

        code = line[0]
        value = line[1:]
        if code == "D":
            record["date"] = value
        elif code == "T":
            record["amount"] = value
        elif code == "P":
            record["description"] = value
        elif code == "N":
            record["reference"] = value

    # Handle last record without ^ terminator
    if "date" in record and "amount" in record:
        record_no += 1
        rows.append(
            {
                "date": _parse_qif_date(record["date"], record_no),
                "amount": _parse_qif_amount(record["amount"], record_no),
                "balance_after": Decimal("0"),
                "description": record.get("description", ""),
                "reference": record.get("reference"),
            }
        )

    if not rows:
        raise BankImportError("no transactions found in QIF file")
    return rows
