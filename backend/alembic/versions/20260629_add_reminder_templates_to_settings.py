"""add reminder email templates to app_settings

Revision ID: e2b8f1a4d6c0
Revises: c7e1a9d3f2b8
Create Date: 2026-06-29 00:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2b8f1a4d6c0"
down_revision: str | None = "c7e1a9d3f2b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = (
    "reminder_first_subject_template",
    "reminder_first_body_template",
    "reminder_next_subject_template",
    "reminder_next_body_template",
)


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        for name in _COLUMNS:
            batch_op.add_column(sa.Column(name, sa.String(length=4000), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        for name in reversed(_COLUMNS):
            batch_op.drop_column(name)
