"""Migration 0038 — add confirmed and confirmed_date to deposits."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0038"
down_revision: str = "0037"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("deposits") as batch_op:
        batch_op.add_column(
            sa.Column("confirmed", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("confirmed_date", sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("deposits") as batch_op:
        batch_op.drop_column("confirmed_date")
        batch_op.drop_column("confirmed")
