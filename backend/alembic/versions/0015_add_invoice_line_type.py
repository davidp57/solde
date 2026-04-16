"""Migration 0015 - add invoice line type."""

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("invoice_lines") as batch_op:
        batch_op.add_column(sa.Column("line_type", sa.String(length=20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("invoice_lines") as batch_op:
        batch_op.drop_column("line_type")
