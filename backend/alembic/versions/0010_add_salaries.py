"""Migration 0010 — add salaries table."""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "salaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("hours", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("gross", sa.Numeric(10, 2), nullable=False),
        sa.Column("employee_charges", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("employer_charges", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("net_pay", sa.Numeric(10, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_salaries_id", "salaries", ["id"])
    op.create_index("ix_salaries_employee_id", "salaries", ["employee_id"])
    op.create_index("ix_salaries_month", "salaries", ["month"])


def downgrade() -> None:
    op.drop_table("salaries")
