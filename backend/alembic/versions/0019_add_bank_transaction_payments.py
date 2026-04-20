"""add bank transaction payments

Revision ID: 0019
Revises: 0018
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_transaction_payments",
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["bank_transactions.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("transaction_id", "payment_id"),
    )
    op.create_index(
        "ix_bank_transaction_payments_payment_id",
        "bank_transaction_payments",
        ["payment_id"],
        unique=False,
    )
    op.execute(
        """
        INSERT INTO bank_transaction_payments (transaction_id, payment_id)
        SELECT id, payment_id
        FROM bank_transactions
        WHERE payment_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_bank_transaction_payments_payment_id", table_name="bank_transaction_payments")
    op.drop_table("bank_transaction_payments")
