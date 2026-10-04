"""add audit_logs.target_label

A human-readable snapshot of the audited target ("15/03/2026 · 150,00 € · VIR
DUPONT"), so the audit journal stays legible and searchable after the target is
edited or deleted. Existing rows are labelled once at startup
(backfill_target_labels), where the application code that builds labels lives.

Revision ID: a4f1c8e2b937
Revises: e3a9c5d1f702
Create Date: 2026-10-04 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4f1c8e2b937"
down_revision: str | None = "e3a9c5d1f702"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.add_column(sa.Column("target_label", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.drop_column("target_label")
