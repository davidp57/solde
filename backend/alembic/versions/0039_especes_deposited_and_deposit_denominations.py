"""Migration 0039 — especes payments auto-deposited; deposit denomination details.

1. Mark all existing especes payments as deposited (cash is always immediately
   in the till — no separate deposit step is needed).
2. Add a JSON ``denomination_details`` column to ``deposits`` for cash
   denomination breakdown (optional, e.g. 3×50€, 4×20€).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039"
down_revision: str = "0038"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add denomination_details to deposits
    with op.batch_alter_table("deposits") as batch_op:
        batch_op.add_column(sa.Column("denomination_details", sa.Text(), nullable=True))

    # 2. Mark existing especes payments as deposited=True, deposit_date=date
    op.execute(
        """
        UPDATE payments
        SET deposited = 1,
            deposit_date = COALESCE(deposit_date, date)
        WHERE method = 'especes'
          AND deposited = 0
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("deposits") as batch_op:
        batch_op.drop_column("denomination_details")

    # Cannot reliably un-set deposited for especes — leave as-is on downgrade.
