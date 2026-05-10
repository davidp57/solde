"""Migration 0053 — add backup settings to app_settings + create backup_destination table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0053"
down_revision: str = "0052"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add backup columns to app_settings
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column("backup_enabled", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column(
                "backup_schedule_type", sa.String(20), nullable=False, server_default="interval"
            )
        )
        batch_op.add_column(
            sa.Column("backup_interval_hours", sa.Integer(), nullable=False, server_default="24")
        )
        batch_op.add_column(sa.Column("backup_cron_expression", sa.String(100), nullable=True))
        batch_op.add_column(
            sa.Column("backup_include_uploads", sa.Boolean(), nullable=False, server_default="1")
        )
        batch_op.add_column(
            sa.Column("backup_notify_on_failure", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("backup_last_run_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("backup_last_run_status", sa.String(20), nullable=True))

    # Create backup_destination table
    op.create_table(
        "backup_destination",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("rclone_remote_name", sa.String(100), nullable=False),
        sa.Column("rclone_config", sa.Text(), nullable=True),
        sa.Column("target_path", sa.String(500), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("backup_destination")
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("backup_last_run_status")
        batch_op.drop_column("backup_last_run_at")
        batch_op.drop_column("backup_notify_on_failure")
        batch_op.drop_column("backup_include_uploads")
        batch_op.drop_column("backup_cron_expression")
        batch_op.drop_column("backup_interval_hours")
        batch_op.drop_column("backup_schedule_type")
        batch_op.drop_column("backup_enabled")
