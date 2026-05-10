"""add backup_last_run_error to app_settings

Revision ID: df93ace219eb
Revises: 0053
Create Date: 2026-05-10 19:35:27.582982+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "df93ace219eb"
down_revision: str | None = "0053"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column("backup_last_run_error", sa.String(length=1000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "backup_last_run_error")
