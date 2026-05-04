"""Migration 0049 — add cheque_number_template to app_settings.

Adds a configurable template for auto-suggesting cheque numbers on payment
entry. Default format: {date}.{seq} (e.g. 20260503.01).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0049"
down_revision: str = "0048"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "cheque_number_template",
                sa.String(100),
                nullable=False,
                server_default="{date}.{seq}",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("cheque_number_template")
