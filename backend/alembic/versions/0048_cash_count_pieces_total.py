"""Migration 0048 — Replace individual coin denomination fields with pieces_total on cash_counts.

Adds a ``pieces_total`` column (Decimal) to ``cash_counts`` and migrates
existing records by summing all the individual coin count fields.
The old coin columns are kept as legacy (values preserved, columns not dropped)
so that any direct DB read of historical records remains coherent.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0048"
down_revision: str = "0047"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cash_counts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "pieces_total",
                sa.Numeric(10, 2),
                nullable=False,
                server_default="0",
            )
        )

    # Migrate existing records: compute pieces_total from the individual coin fields
    op.execute(
        """
        UPDATE cash_counts
        SET pieces_total = ROUND(
            (   count_2       * 200
              + count_1       * 100
              + count_cents_50 * 50
              + count_cents_20 * 20
              + count_cents_10 * 10
              + count_cents_5  *  5
              + count_cents_2  *  2
              + count_cents_1  *  1
            ) / 100.0,
            2
        )
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("cash_counts") as batch_op:
        batch_op.drop_column("pieces_total")
