"""add payments table

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("cheque_number", sa.String(50), nullable=True),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("deposited", sa.Boolean(), nullable=False),
        sa.Column("deposit_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_id", "payments", ["id"], unique=False)
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"], unique=False)
    op.create_index("ix_payments_contact_id", "payments", ["contact_id"], unique=False)
    op.create_index("ix_payments_date", "payments", ["date"], unique=False)
    op.create_index("ix_payments_method", "payments", ["method"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payments_method", table_name="payments")
    op.drop_index("ix_payments_date", table_name="payments")
    op.drop_index("ix_payments_contact_id", table_name="payments")
    op.drop_index("ix_payments_invoice_id", table_name="payments")
    op.drop_index("ix_payments_id", table_name="payments")
    op.drop_table("payments")
