"""The monthly checklist itself — its blocks, its steps, and their order.

The list is code, not data: it is versioned with the application and evolves
with the user manual, the way a manufacturer's checklist does.  Labels live in
the frontend's i18n file, keyed by the identifiers below.

Ordering principle, established with the user: **one single visit per external
destination**, everything that determines that visit being done beforehand.
The three external destinations are the payroll platform (CEA) and the bank's
website, visited once for transfers *and* the statement download.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ChecklistBlock(StrEnum):
    #: Only rendered when the previous session was closed with unchecked steps.
    CARRYOVER = "carryover"
    ENTRY = "entry"
    PAYROLL = "payroll"
    BANK_VISIT = "bank_visit"
    STATEMENT = "statement"
    CASH = "cash"
    DEPOSITS = "deposits"
    CLOSING = "closing"


class ChecklistSignal(StrEnum):
    """Facts the application can observe about a step.

    A signal is *shown next to* a step, never used to tick it: a checklist is
    there to verify, not to note down. Steps that call for judgement — whether
    every supplier invoice of the month has been entered — have no signal, and
    neither do the external ones.
    """

    LAST_IMPORT = "last_import"
    SALARY_SLIPS = "salary_slips"
    UNRECONCILED = "unreconciled"
    LAST_CASH_COUNT = "last_cash_count"
    PENDING_CASH = "pending_cash"
    PENDING_CHEQUES = "pending_cheques"
    LAST_BACKUP = "last_backup"


@dataclass(frozen=True)
class ChecklistStep:
    key: str
    block: ChecklistBlock
    #: Done outside the application: nothing here can observe it.
    external: bool = False
    signal: ChecklistSignal | None = None
    #: Route name the frontend sends the user to, when the step is done in-app.
    route: str | None = None


#: The canonical list. Order matters — it is the order of the session.
CHECKLIST_STEPS: tuple[ChecklistStep, ...] = (
    # 1. Entry
    ChecklistStep("supplier_invoices", ChecklistBlock.ENTRY, route="invoices-supplier"),
    # 2. Payroll
    ChecklistStep("cea_payroll", ChecklistBlock.PAYROLL, external=True),
    ChecklistStep(
        "salary_slips",
        ChecklistBlock.PAYROLL,
        signal=ChecklistSignal.SALARY_SLIPS,
        route="salaries",
    ),
    # 3. The single visit to the bank's website
    ChecklistStep("transfer_salaries", ChecklistBlock.BANK_VISIT, external=True),
    ChecklistStep("transfer_suppliers", ChecklistBlock.BANK_VISIT, external=True),
    ChecklistStep("download_statement", ChecklistBlock.BANK_VISIT, external=True),
    # 4. Statement
    ChecklistStep(
        "import_statement",
        ChecklistBlock.STATEMENT,
        signal=ChecklistSignal.LAST_IMPORT,
        route="bank",
    ),
    ChecklistStep("check_categories", ChecklistBlock.STATEMENT, route="bank"),
    ChecklistStep("create_client_payments", ChecklistBlock.STATEMENT, route="bank"),
    ChecklistStep(
        "reconcile",
        ChecklistBlock.STATEMENT,
        signal=ChecklistSignal.UNRECONCILED,
        route="bank",
    ),
    ChecklistStep("compare_balance", ChecklistBlock.STATEMENT, route="bank"),
    # 5. Cash — everything that moves the till, then counting it. Counting before
    # the last movement is entered would compare the drawer against a stale total.
    ChecklistStep("supplier_cash_payments", ChecklistBlock.CASH, route="invoices-supplier"),
    ChecklistStep("cash_movements", ChecklistBlock.CASH, route="cash"),
    ChecklistStep(
        "cash_count",
        ChecklistBlock.CASH,
        signal=ChecklistSignal.LAST_CASH_COUNT,
        route="cash",
    ),
    # 6. Deposit slips — prepared in the Bank screen, not the till's.
    ChecklistStep(
        "prepare_cash_slip",
        ChecklistBlock.DEPOSITS,
        signal=ChecklistSignal.PENDING_CASH,
        route="bank",
    ),
    ChecklistStep(
        "prepare_cheque_slip",
        ChecklistBlock.DEPOSITS,
        signal=ChecklistSignal.PENDING_CHEQUES,
        route="bank",
    ),
    # 7. Closing
    ChecklistStep(
        "check_backup",
        ChecklistBlock.CLOSING,
        signal=ChecklistSignal.LAST_BACKUP,
        route="settings",
    ),
)

STEP_KEYS: frozenset[str] = frozenset(step.key for step in CHECKLIST_STEPS)

STEPS_BY_KEY: dict[str, ChecklistStep] = {step.key: step for step in CHECKLIST_STEPS}
