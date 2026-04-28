"""Migration 0040 — add in_deposit column to payments.

Introduces an intermediate state for cheque payments:
  deposited=False, in_deposit=False  → not yet in any deposit slip (à déposer)
  deposited=False, in_deposit=True   → assigned to an unconfirmed deposit slip (en transit)
  deposited=True,  in_deposit=False  → fully confirmed and deposited
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0040"
down_revision: str = "0039"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("payments") as batch_op:
        batch_op.add_column(
            sa.Column("in_deposit", sa.Boolean(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("payments") as batch_op:
        batch_op.drop_column("in_deposit")
