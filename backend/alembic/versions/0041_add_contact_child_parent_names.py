"""Migration 0041 — add child/parent name fields to contacts.

Adds four optional text columns to the contacts table:
  child_first_name, child_last_name — first and last name of the child (for client contacts).
  other_parent_first_name, other_parent_last_name — first and last name of the other parent.
All four are nullable and only relevant for CLIENT-type contacts.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0041"
down_revision: str = "0040"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.add_column(sa.Column("child_first_name", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("child_last_name", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("other_parent_first_name", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("other_parent_last_name", sa.String(100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.drop_column("other_parent_last_name")
        batch_op.drop_column("other_parent_first_name")
        batch_op.drop_column("child_last_name")
        batch_op.drop_column("child_first_name")
