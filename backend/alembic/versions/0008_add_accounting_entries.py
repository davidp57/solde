"""Migration 0008 — add accounting_entries table."""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounting_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entry_number", sa.String(20), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("account_number", sa.String(20), nullable=False),
        sa.Column("label", sa.Text(), nullable=False, server_default=""),
        sa.Column("debit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column(
            "fiscal_year_id",
            sa.Integer(),
            sa.ForeignKey("fiscal_years.id"),
            nullable=True,
        ),
        sa.Column("source_type", sa.String(20), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_accounting_entries_entry_number", "accounting_entries", ["entry_number"])
    op.create_index("ix_accounting_entries_date", "accounting_entries", ["date"])
    op.create_index(
        "ix_accounting_entries_account_number", "accounting_entries", ["account_number"]
    )
    op.create_index(
        "ix_accounting_entries_fiscal_year_id", "accounting_entries", ["fiscal_year_id"]
    )
    op.create_index("ix_accounting_entries_source_type", "accounting_entries", ["source_type"])
    op.create_index("ix_accounting_entries_source_id", "accounting_entries", ["source_id"])


def downgrade() -> None:
    op.drop_table("accounting_entries")
