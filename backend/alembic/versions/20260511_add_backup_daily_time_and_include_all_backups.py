"""add backup_daily_time and backup_include_all_backups columns

Revision ID: a3f8c2d1b904
Revises: df93ace219eb
Create Date: 2026-05-11 13:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f8c2d1b904"
down_revision: str | None = "df93ace219eb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "backup_daily_time",
                sa.String(length=5),
                nullable=True,
                server_default="02:00",
            )
        )
        batch_op.add_column(
            sa.Column(
                "backup_include_all_backups",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("backup_include_all_backups")
        batch_op.drop_column("backup_daily_time")
