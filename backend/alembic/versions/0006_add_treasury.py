"""add cash_register, cash_counts, bank_transactions, deposits, deposit_payments tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cash_register",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("type", sa.String(5), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("balance_after", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cash_register_id", "cash_register", ["id"], unique=False)
    op.create_index("ix_cash_register_date", "cash_register", ["date"], unique=False)
    op.create_index("ix_cash_register_type", "cash_register", ["type"], unique=False)
    op.create_index("ix_cash_register_contact_id", "cash_register", ["contact_id"], unique=False)
    op.create_index("ix_cash_register_payment_id", "cash_register", ["payment_id"], unique=False)

    op.create_table(
        "cash_counts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("count_100", sa.Integer(), nullable=False),
        sa.Column("count_50", sa.Integer(), nullable=False),
        sa.Column("count_20", sa.Integer(), nullable=False),
        sa.Column("count_10", sa.Integer(), nullable=False),
        sa.Column("count_5", sa.Integer(), nullable=False),
        sa.Column("count_2", sa.Integer(), nullable=False),
        sa.Column("count_1", sa.Integer(), nullable=False),
        sa.Column("count_cents_50", sa.Integer(), nullable=False),
        sa.Column("count_cents_20", sa.Integer(), nullable=False),
        sa.Column("count_cents_10", sa.Integer(), nullable=False),
        sa.Column("count_cents_5", sa.Integer(), nullable=False),
        sa.Column("count_cents_2", sa.Integer(), nullable=False),
        sa.Column("count_cents_1", sa.Integer(), nullable=False),
        sa.Column("total_counted", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance_expected", sa.Numeric(10, 2), nullable=False),
        sa.Column("difference", sa.Numeric(10, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cash_counts_id", "cash_counts", ["id"], unique=False)
    op.create_index("ix_cash_counts_date", "cash_counts", ["date"], unique=False)

    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("balance_after", sa.Numeric(10, 2), nullable=False),
        sa.Column("reconciled", sa.Boolean(), nullable=False),
        sa.Column("reconciled_with", sa.String(100), nullable=True),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bank_transactions_id", "bank_transactions", ["id"], unique=False)
    op.create_index("ix_bank_transactions_date", "bank_transactions", ["date"], unique=False)
    op.create_index(
        "ix_bank_transactions_reconciled",
        "bank_transactions",
        ["reconciled"],
        unique=False,
    )

    op.create_table(
        "deposits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("bank_reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deposits_id", "deposits", ["id"], unique=False)
    op.create_index("ix_deposits_date", "deposits", ["date"], unique=False)
    op.create_index("ix_deposits_type", "deposits", ["type"], unique=False)

    op.create_table(
        "deposit_payments",
        sa.Column("deposit_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["deposit_id"], ["deposits.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("deposit_id", "payment_id"),
    )


def downgrade() -> None:
    op.drop_table("deposit_payments")
    op.drop_index("ix_deposits_type", table_name="deposits")
    op.drop_index("ix_deposits_date", table_name="deposits")
    op.drop_index("ix_deposits_id", table_name="deposits")
    op.drop_table("deposits")
    op.drop_index("ix_bank_transactions_reconciled", table_name="bank_transactions")
    op.drop_index("ix_bank_transactions_date", table_name="bank_transactions")
    op.drop_index("ix_bank_transactions_id", table_name="bank_transactions")
    op.drop_table("bank_transactions")
    op.drop_index("ix_cash_counts_date", table_name="cash_counts")
    op.drop_index("ix_cash_counts_id", table_name="cash_counts")
    op.drop_table("cash_counts")
    op.drop_index("ix_cash_register_payment_id", table_name="cash_register")
    op.drop_index("ix_cash_register_contact_id", table_name="cash_register")
    op.drop_index("ix_cash_register_type", table_name="cash_register")
    op.drop_index("ix_cash_register_date", table_name="cash_register")
    op.drop_index("ix_cash_register_id", table_name="cash_register")
    op.drop_table("cash_register")
