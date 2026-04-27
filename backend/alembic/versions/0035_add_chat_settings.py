"""Migration 0035 — add chat provider settings to app_settings."""

import sqlalchemy as sa
from alembic import op

revision: str = "0035"
down_revision: str = "0034"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column("chat_provider", sa.String(50), nullable=False, server_default="gemini"),
    )
    op.add_column(
        "app_settings",
        sa.Column("chat_api_key", sa.String(500), nullable=True),
    )
    op.add_column(
        "app_settings",
        sa.Column("chat_model", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "chat_model")
    op.drop_column("app_settings", "chat_api_key")
    op.drop_column("app_settings", "chat_provider")
