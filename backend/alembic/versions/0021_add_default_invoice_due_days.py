"""Migration 0021 — add default invoice due days setting."""

import sqlalchemy as sa
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column("default_invoice_due_days", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "default_invoice_due_days")
