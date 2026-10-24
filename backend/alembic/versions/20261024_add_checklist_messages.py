"""add checklist messages

Notes any user can leave for the accountant, shown at the top of the monthly
checklist until they are ticked.

Revision ID: 5b8e2d7c1f46
Revises: a4f1c8e2b937
Create Date: 2026-10-24 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5b8e2d7c1f46"
down_revision: str | None = "a4f1c8e2b937"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "checklist_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("checked_by", sa.String(length=100), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["checklist_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_checklist_messages_id"), "checklist_messages", ["id"])
    op.create_index(op.f("ix_checklist_messages_session_id"), "checklist_messages", ["session_id"])
    op.create_index(op.f("ix_checklist_messages_checked"), "checklist_messages", ["checked"])


def downgrade() -> None:
    op.drop_index(op.f("ix_checklist_messages_checked"), table_name="checklist_messages")
    op.drop_index(op.f("ix_checklist_messages_session_id"), table_name="checklist_messages")
    op.drop_index(op.f("ix_checklist_messages_id"), table_name="checklist_messages")
    op.drop_table("checklist_messages")
