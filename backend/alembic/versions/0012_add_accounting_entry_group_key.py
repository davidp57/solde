"""Migration 0012 — add accounting entry group key."""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("accounting_entries") as batch_op:
        batch_op.add_column(sa.Column("group_key", sa.String(length=80), nullable=True))
        batch_op.create_index("ix_accounting_entries_group_key", ["group_key"])

    op.execute(
        """
        UPDATE accounting_entries
        SET group_key = source_type || ':' || source_id
        WHERE source_type IS NOT NULL AND source_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE accounting_entries
        SET group_key = 'legacy:' || id
        WHERE group_key IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("accounting_entries") as batch_op:
        batch_op.drop_index("ix_accounting_entries_group_key")
        batch_op.drop_column("group_key")
