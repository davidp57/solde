"""Migration 0036 — create chat_log table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0036"
down_revision: str = "0035"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "asked_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
    )
    op.create_index("ix_chat_log_user_id", "chat_log", ["user_id"])
    op.create_index("ix_chat_log_asked_at", "chat_log", ["asked_at"])


def downgrade() -> None:
    op.drop_index("ix_chat_log_asked_at", table_name="chat_log")
    op.drop_index("ix_chat_log_user_id", table_name="chat_log")
    op.drop_table("chat_log")
