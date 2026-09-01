"""add monthly checklist sessions and step states

Revision ID: c7d2f1a34b90
Revises: a1c4e9b70d38
Create Date: 2026-09-01 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d2f1a34b90"
down_revision: str | None = "a1c4e9b70d38"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "checklist_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("period_type", sa.String(length=10), nullable=False, server_default="monthly"),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("opened_by", sa.String(length=100), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("closed_by", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("period_type", "period", name="uq_checklist_period"),
    )
    op.create_index(op.f("ix_checklist_sessions_id"), "checklist_sessions", ["id"])
    op.create_index(op.f("ix_checklist_sessions_period"), "checklist_sessions", ["period"])
    op.create_index(op.f("ix_checklist_sessions_status"), "checklist_sessions", ["status"])

    op.create_table(
        "checklist_step_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("step_key", sa.String(length=50), nullable=False),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("checked_by", sa.String(length=100), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=True),
        sa.Column("carried_over", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["session_id"], ["checklist_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "step_key", name="uq_checklist_step"),
    )
    op.create_index(op.f("ix_checklist_step_states_id"), "checklist_step_states", ["id"])
    op.create_index(
        op.f("ix_checklist_step_states_session_id"), "checklist_step_states", ["session_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_checklist_step_states_session_id"), table_name="checklist_step_states")
    op.drop_index(op.f("ix_checklist_step_states_id"), table_name="checklist_step_states")
    op.drop_table("checklist_step_states")
    op.drop_index(op.f("ix_checklist_sessions_status"), table_name="checklist_sessions")
    op.drop_index(op.f("ix_checklist_sessions_period"), table_name="checklist_sessions")
    op.drop_index(op.f("ix_checklist_sessions_id"), table_name="checklist_sessions")
    op.drop_table("checklist_sessions")
