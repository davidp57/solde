"""add bank transaction payment link

Revision ID: 0018
Revises: 0017
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("bank_transactions") as batch_op:
        batch_op.add_column(sa.Column("payment_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_bank_transactions_payment_id", ["payment_id"])
        batch_op.create_foreign_key(
            "fk_bank_transactions_payment_id_payments",
            "payments",
            ["payment_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("bank_transactions") as batch_op:
        batch_op.drop_constraint("fk_bank_transactions_payment_id_payments", type_="foreignkey")
        batch_op.drop_index("ix_bank_transactions_payment_id")
        batch_op.drop_column("payment_id")
