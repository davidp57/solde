"""Migration 0051 — add bank ACCTID settings.

Adds two columns to app_settings for mapping OFX ACCTID values to
bank accounts (courant / epargne).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0051"
down_revision: str = "0050"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "bank_account_courant_acctid",
                sa.String(50),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "bank_account_epargne_acctid",
                sa.String(50),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("bank_account_epargne_acctid")
        batch_op.drop_column("bank_account_courant_acctid")
