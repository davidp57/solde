#!/usr/bin/env python3
"""One-shot script: generate accounting entries for two unreconciled deposit
bank transactions imported via OFX (14/04/2026).

Context
-------
These two transactions were imported from the OFX file but were never matched
to a Deposit slip because the deposit was done outside the application (funds
recorded in the Excel file).  No accounting entries were generated for them.

Transactions targeted
---------------------
- +530.00 € — REM CHQ REF05001A05  (detected_category = cheque_deposit)
  → trigger DEPOSIT_CHEQUES : 512100 D / 511200 C
  → marks all undeposited cheque payments as deposited = True
- +800.00 € — VRST REF05001A05     (detected_category = cash_deposit)
  → trigger DEPOSIT_ESPECES : 512100 D / 531000 C
  → creates a CashRegister OUT entry (cash left the till for the bank)

Both transactions are then marked as reconciled.

Usage (from repo root, with venv active)
-----------------------------------------
    python scripts/fix_bank_deposits_14apr2026.py          # dry-run (default)
    python scripts/fix_bank_deposits_14apr2026.py --commit  # apply changes
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# Ensure repo root is on sys.path so backend imports work.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models.accounting_entry import AccountingEntry, EntrySourceType
from backend.models.bank import BankTransaction, BankTransactionCategory
from backend.models.cash import CashEntrySource, CashMovementType
from backend.models.payment import Payment, PaymentMethod
from backend.models.accounting_rule import TriggerType
from backend.services import accounting_engine
from backend.services.cash_service import create_cash_entry_record

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TARGET_DATE = date(2026, 4, 14)
CHQ_AMOUNT = Decimal("530.00")
ESP_AMOUNT = Decimal("800.00")
ESP_DESCRIPTION = "Remise d'espèces en banque 14/04/2026"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _find_tx(
    db: AsyncSession,
    category: BankTransactionCategory,
    amount: Decimal,
) -> BankTransaction | None:
    result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.date == TARGET_DATE,
            BankTransaction.detected_category == category,
            BankTransaction.amount == amount,
        )
    )
    return result.scalar_one_or_none()


async def _has_entries(db: AsyncSession, tx: BankTransaction) -> bool:
    result = await db.execute(
        select(AccountingEntry).where(
            AccountingEntry.source_type == EntrySourceType.BANK_TRANSACTION,
            AccountingEntry.source_id == tx.id,
        )
    )
    return result.scalar_one_or_none() is not None


async def _undeposited_cheque_payments(db: AsyncSession) -> list[Payment]:
    result = await db.execute(
        select(Payment).where(
            Payment.method == PaymentMethod.CHEQUE,
            Payment.deposited.is_(False),
        )
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


async def run(commit: bool) -> None:
    mode = "COMMIT" if commit else "DRY-RUN"
    print(f"Mode : {mode}\n")

    async with get_session() as db:
        # ---------------------------------------------------------------
        # 1. Cheque deposit — +530 €
        # ---------------------------------------------------------------
        tx_chq = await _find_tx(db, BankTransactionCategory.CHEQUE_DEPOSIT, CHQ_AMOUNT)
        if tx_chq is None:
            print(
                f"ERREUR : aucune transaction cheque_deposit de {CHQ_AMOUNT} € le {TARGET_DATE}."
            )
            print("  Vérifier la date ou le montant dans la base.")
            sys.exit(1)

        print(f"TX chèques trouvée : id={tx_chq.id}  réconciliée={tx_chq.reconciled}")

        if tx_chq.reconciled:
            print("  → déjà rapprochée, ignorée.")
        else:
            already = await _has_entries(db, tx_chq)
            if already:
                print("  → écritures déjà présentes, on rapproche uniquement.")
            else:
                context = {
                    "label": tx_chq.description or tx_chq.reference or "",
                    "amount": str(CHQ_AMOUNT),
                    "date": str(TARGET_DATE),
                    "reference": tx_chq.reference or "",
                }
                if commit:
                    entries = await accounting_engine.generate_entries_for_trigger(
                        db,
                        TriggerType.DEPOSIT_CHEQUES,
                        CHQ_AMOUNT,
                        TARGET_DATE,
                        context,
                        source_type=EntrySourceType.BANK_TRANSACTION,
                        source_id=tx_chq.id,
                    )
                    print(f"  → {len(entries)} écriture(s) générées (DEPOSIT_CHEQUES).")
                else:
                    print(
                        f"  → [DRY-RUN] générerait les écritures DEPOSIT_CHEQUES "
                        f"(512100 D / 511200 C, {CHQ_AMOUNT} €)."
                    )

            # Mark undeposited cheque payments as deposited
            cheque_pmts = await _undeposited_cheque_payments(db)
            total = sum(p.amount for p in cheque_pmts)
            print(
                f"  Paiements chèque non déposés : {len(cheque_pmts)} "
                f"(total {total} €)"
            )
            if total != CHQ_AMOUNT:
                print(
                    f"  AVERTISSEMENT : total {total} € ≠ montant TX {CHQ_AMOUNT} €. "
                    "Vérifier manuellement avant de committer."
                )
            for p in cheque_pmts:
                print(f"    - paiement id={p.id}  {p.date}  {p.amount} €")
                if commit:
                    p.deposited = True
                    p.in_deposit = False

            if commit:
                tx_chq.reconciled = True
                print("  → TX chèques rapprochée.")
            else:
                print("  → [DRY-RUN] marquerait la TX comme rapprochée.")

        print()

        # ---------------------------------------------------------------
        # 2. Cash deposit — +800 €
        # ---------------------------------------------------------------
        tx_esp = await _find_tx(db, BankTransactionCategory.CASH_DEPOSIT, ESP_AMOUNT)
        if tx_esp is None:
            print(
                f"ERREUR : aucune transaction cash_deposit de {ESP_AMOUNT} € le {TARGET_DATE}."
            )
            print("  Vérifier la date ou le montant dans la base.")
            sys.exit(1)

        print(f"TX espèces trouvée : id={tx_esp.id}  réconciliée={tx_esp.reconciled}")

        if tx_esp.reconciled:
            print("  → déjà rapprochée, ignorée.")
        else:
            already = await _has_entries(db, tx_esp)
            if already:
                print("  → écritures déjà présentes, on rapproche uniquement.")
            else:
                context = {
                    "label": ESP_DESCRIPTION,
                    "amount": str(ESP_AMOUNT),
                    "date": str(TARGET_DATE),
                    "reference": tx_esp.reference or "",
                }
                if commit:
                    entries = await accounting_engine.generate_entries_for_trigger(
                        db,
                        TriggerType.DEPOSIT_ESPECES,
                        ESP_AMOUNT,
                        TARGET_DATE,
                        context,
                        source_type=EntrySourceType.BANK_TRANSACTION,
                        source_id=tx_esp.id,
                    )
                    print(f"  → {len(entries)} écriture(s) générées (DEPOSIT_ESPECES).")
                else:
                    print(
                        f"  → [DRY-RUN] générerait les écritures DEPOSIT_ESPECES "
                        f"(512100 D / 531000 C, {ESP_AMOUNT} €)."
                    )

            # Create missing cash OUT entry
            if commit:
                cash_entry = await create_cash_entry_record(
                    db,
                    date=TARGET_DATE,
                    amount=ESP_AMOUNT,
                    type=CashMovementType.OUT,
                    reference=tx_esp.description or tx_esp.reference or "REF05001A05",
                    description=ESP_DESCRIPTION,
                    source=CashEntrySource.DEPOSIT,
                )
                print(f"  → Sortie caisse créée : id={cash_entry.id}.")
                tx_esp.reconciled = True
                print("  → TX espèces rapprochée.")
            else:
                print(
                    f"  → [DRY-RUN] créerait une sortie caisse OUT {ESP_AMOUNT} € "
                    f"(source=deposit, '{ESP_DESCRIPTION}')."
                )
                print("  → [DRY-RUN] marquerait la TX comme rapprochée.")

        print()
        if not commit:
            # Rollback is handled by get_session on exception; force abort here.
            raise _DryRunAbort()
        print("Terminé.")


class _DryRunAbort(Exception):
    """Signal to abort dry-run without touching the DB."""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix bank deposits 14/04/2026 — generate missing accounting entries."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Apply changes to the database (default: dry-run).",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run(commit=args.commit))
    except _DryRunAbort:
        print("Dry-run terminé — aucune modification effectuée.")
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERREUR inattendue : {exc}")
        raise


if __name__ == "__main__":
    main()
