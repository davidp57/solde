"""Migration 0013 — add cash register source marker."""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("cash_register") as batch_op:
        batch_op.add_column(
            sa.Column(
                "source",
                sa.String(length=20),
                nullable=False,
                server_default="manual",
            )
        )
        batch_op.create_index("ix_cash_register_source", ["source"])

    op.execute(
        """
        UPDATE cash_register
        SET source = 'system_opening'
        WHERE description = 'Ouverture du système'
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("cash_register") as batch_op:
        batch_op.drop_index("ix_cash_register_source")
        batch_op.drop_column("source")
