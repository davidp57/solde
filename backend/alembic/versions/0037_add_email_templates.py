"""Migration 0037 — add email_subject_template and email_body_template to app_settings."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0037"
down_revision: str = "0036"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(sa.Column("email_subject_template", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("email_body_template", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("email_body_template")
        batch_op.drop_column("email_subject_template")
