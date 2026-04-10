"""Migration 0009 — add accounting_rules and accounting_rule_entries tables."""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounting_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_accounting_rules_trigger_type", "accounting_rules", ["trigger_type"]
    )

    op.create_table(
        "accounting_rule_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "rule_id",
            sa.Integer(),
            sa.ForeignKey("accounting_rules.id"),
            nullable=False,
        ),
        sa.Column("account_number", sa.String(20), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column(
            "description_template",
            sa.String(500),
            nullable=False,
            server_default="{{label}}",
        ),
    )
    op.create_index(
        "ix_accounting_rule_entries_rule_id", "accounting_rule_entries", ["rule_id"]
    )


def downgrade() -> None:
    op.drop_table("accounting_rule_entries")
    op.drop_table("accounting_rules")
