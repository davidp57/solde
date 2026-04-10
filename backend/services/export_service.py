"""Export service — CSV and PDF exports for accounting reports."""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def _write_csv(headers: list[str], rows: list[list[Any]]) -> bytes:
    """Serialize rows to CSV bytes (UTF-8 with BOM for Excel compat)."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    writer.writerows(rows)
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


async def export_journal_csv(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    account_number: str | None = None,
    fiscal_year_id: int | None = None,
) -> bytes:
    """Export journal entries to CSV."""
    from backend.services.accounting_entry_service import get_journal  # noqa: PLC0415

    entries = await get_journal(
        db,
        from_date=from_date,
        to_date=to_date,
        account_number=account_number,
        fiscal_year_id=fiscal_year_id,
        limit=100_000,
    )

    headers = ["N° pièce", "Date", "Compte", "Libellé", "Débit", "Crédit", "Source"]
    rows = [
        [
            e.entry_number,
            e.date.strftime("%d/%m/%Y"),
            e.account_number,
            e.label,
            f"{Decimal(str(e.debit)):.2f}".replace(".", ","),
            f"{Decimal(str(e.credit)):.2f}".replace(".", ","),
            e.source_type or "",
        ]
        for e in entries
    ]
    return _write_csv(headers, rows)


async def export_balance_csv(
    db: AsyncSession,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    fiscal_year_id: int | None = None,
) -> bytes:
    """Export balance to CSV."""
    from backend.services.accounting_entry_service import get_balance  # noqa: PLC0415

    rows_data = await get_balance(
        db, from_date=from_date, to_date=to_date, fiscal_year_id=fiscal_year_id
    )

    headers = ["Compte", "Libellé", "Type", "Débit", "Crédit", "Solde"]
    rows = [
        [
            r.account_number,
            r.account_label,
            r.account_type,
            f"{r.total_debit:.2f}".replace(".", ","),
            f"{r.total_credit:.2f}".replace(".", ","),
            f"{r.solde:.2f}".replace(".", ","),
        ]
        for r in rows_data
    ]
    return _write_csv(headers, rows)


async def export_resultat_csv(
    db: AsyncSession, fiscal_year_id: int | None = None
) -> bytes:
    """Export compte de résultat to CSV."""
    from backend.services.accounting_entry_service import get_resultat  # noqa: PLC0415

    data = await get_resultat(db, fiscal_year_id=fiscal_year_id)

    headers = ["Section", "Compte", "Libellé", "Montant"]
    rows: list[list[Any]] = []
    for r in data.charges:
        rows.append(
            [
                "Charges",
                r.account_number,
                r.account_label,
                f"{r.solde:.2f}".replace(".", ","),
            ]
        )
    rows.append(
        ["TOTAL CHARGES", "", "", f"{data.total_charges:.2f}".replace(".", ",")]
    )
    for r in data.produits:
        rows.append(
            [
                "Produits",
                r.account_number,
                r.account_label,
                f"{r.solde:.2f}".replace(".", ","),
            ]
        )
    rows.append(
        ["TOTAL PRODUITS", "", "", f"{data.total_produits:.2f}".replace(".", ",")]
    )
    rows.append(["RÉSULTAT", "", "", f"{data.resultat:.2f}".replace(".", ",")])
    return _write_csv(headers, rows)


async def export_bilan_csv(
    db: AsyncSession, fiscal_year_id: int | None = None
) -> bytes:
    """Export simplified bilan to CSV."""
    from backend.services.accounting_entry_service import get_bilan  # noqa: PLC0415

    data = await get_bilan(db, fiscal_year_id=fiscal_year_id)

    headers = ["Section", "Compte", "Libellé", "Solde"]
    rows: list[list[Any]] = []
    for r in data.actif:
        rows.append(
            [
                "Actif",
                r.account_number,
                r.account_label,
                f"{r.solde:.2f}".replace(".", ","),
            ]
        )
    rows.append(["TOTAL ACTIF", "", "", f"{data.total_actif:.2f}".replace(".", ",")])
    for r in data.passif:
        rows.append(
            [
                "Passif",
                r.account_number,
                r.account_label,
                f"{r.solde:.2f}".replace(".", ","),
            ]
        )
    rows.append(
        ["Résultat de l'exercice", "", "", f"{data.resultat:.2f}".replace(".", ",")]
    )
    rows.append(["TOTAL PASSIF", "", "", f"{data.total_passif:.2f}".replace(".", ",")])
    return _write_csv(headers, rows)
