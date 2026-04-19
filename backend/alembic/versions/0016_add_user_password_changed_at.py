"""Migration 0016 - add user password changed timestamp."""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_changed_at", sa.DateTime(), nullable=True))

    update_password_changed_at = sa.text(
        "UPDATE users SET password_changed_at = :timestamp WHERE password_changed_at IS NULL"
    )
    op.execute(
        update_password_changed_at.bindparams(timestamp=datetime.now(UTC).replace(tzinfo=None))
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("password_changed_at", existing_type=sa.DateTime(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_changed_at")
