"""add backup_pdfs_only_archived to app_settings

Revision ID: f3a9c0e7b215
Revises: e2b8f1a4d6c0
Create Date: 2026-06-29 02:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a9c0e7b215"
down_revision: str | None = "e2b8f1a4d6c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "backup_pdfs_only_archived",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("backup_pdfs_only_archived")
