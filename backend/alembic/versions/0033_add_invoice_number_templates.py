"""Migration 0033 — add invoice number template settings."""

import sqlalchemy as sa
from alembic import op

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column(
            "client_invoice_number_template",
            sa.String(100),
            nullable=False,
            server_default="{year}-{seq}",
        ),
    )
    op.add_column(
        "app_settings",
        sa.Column(
            "supplier_invoice_number_template",
            sa.String(100),
            nullable=False,
            server_default="FF-%Y%m%d%H.%M.%S",
        ),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "supplier_invoice_number_template")
    op.drop_column("app_settings", "client_invoice_number_template")
