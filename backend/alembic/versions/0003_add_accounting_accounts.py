"""add accounting_accounts table

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounting_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("parent_number", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounting_accounts_id", "accounting_accounts", ["id"], unique=False)
    op.create_index("ix_accounting_accounts_number", "accounting_accounts", ["number"], unique=True)
    op.create_index("ix_accounting_accounts_type", "accounting_accounts", ["type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_accounting_accounts_type", table_name="accounting_accounts")
    op.drop_index("ix_accounting_accounts_number", table_name="accounting_accounts")
    op.drop_index("ix_accounting_accounts_id", table_name="accounting_accounts")
    op.drop_table("accounting_accounts")
