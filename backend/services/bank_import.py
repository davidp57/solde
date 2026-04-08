"""CSV import service for Crédit Mutuel bank statements."""

from __future__ import annotations

import csv
import io
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
