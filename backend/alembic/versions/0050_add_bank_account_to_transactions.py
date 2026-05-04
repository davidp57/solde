"""Migration 0050 — add bank_account column to bank_transactions.

Adds a 'bank_account' column (courant / epargne) to bank_transactions.
All existing rows default to 'courant'.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0050"
down_revision: str = "0049"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("bank_transactions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "bank_account",
                sa.String(10),
                nullable=False,
                server_default="courant",
            )
        )
        batch_op.create_index("ix_bank_transactions_bank_account", ["bank_account"])


def downgrade() -> None:
    with op.batch_alter_table("bank_transactions") as batch_op:
        batch_op.drop_index("ix_bank_transactions_bank_account")
        batch_op.drop_column("bank_account")
