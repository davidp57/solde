"""add bank transaction category

Revision ID: 0017
Revises: 0016
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("bank_transactions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "detected_category",
                sa.String(length=30),
                nullable=False,
                server_default="uncategorized",
            )
        )
        batch_op.create_index("ix_bank_transactions_detected_category", ["detected_category"])


def downgrade() -> None:
    with op.batch_alter_table("bank_transactions") as batch_op:
        batch_op.drop_index("ix_bank_transactions_detected_category")
        batch_op.drop_column("detected_category")
