"""Add smtp_bcc column to app_settings.

Revision ID: 0029
Revises: 0028
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0029"
down_revision: str | None = "0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("app_settings", sa.Column("smtp_bcc", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("app_settings", "smtp_bcc")
