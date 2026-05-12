"""add list_default_limit to app_settings

Revision ID: b5c2d4e1f023
Revises: a3f8c2d1b904
Create Date: 2026-05-12 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5c2d4e1f023"
down_revision: str | None = "a3f8c2d1b904"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "list_default_limit",
                sa.Integer(),
                nullable=False,
                server_default="500",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("list_default_limit")
