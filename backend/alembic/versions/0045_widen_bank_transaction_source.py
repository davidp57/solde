"""Migration 0045 — widen bank_transactions.source column for new import sources.

Extends String(10) → String(20) to accommodate new source values:
  import_excel, import_ofx, import_csv, import_qif
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0045"
down_revision: str = "0044"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("bank_transactions") as batch_op:
        batch_op.alter_column(
            "source",
            existing_type=sa.String(10),
            type_=sa.String(20),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("bank_transactions") as batch_op:
        batch_op.alter_column(
            "source",
            existing_type=sa.String(20),
            type_=sa.String(10),
            nullable=False,
        )
