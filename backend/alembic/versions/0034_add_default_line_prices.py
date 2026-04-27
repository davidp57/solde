"""Migration 0034 — add default unit prices per invoice line type."""

import sqlalchemy as sa
from alembic import op

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_settings", sa.Column("default_price_cours", sa.Numeric(10, 2), nullable=True)
    )
    op.add_column(
        "app_settings", sa.Column("default_price_adhesion", sa.Numeric(10, 2), nullable=True)
    )
    op.add_column(
        "app_settings", sa.Column("default_price_autres", sa.Numeric(10, 2), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("app_settings", "default_price_autres")
    op.drop_column("app_settings", "default_price_adhesion")
    op.drop_column("app_settings", "default_price_cours")
