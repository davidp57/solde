"""Migration 0011 — add import logs table."""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_logs_id", "import_logs", ["id"])
    op.create_index("ix_import_logs_import_type", "import_logs", ["import_type"])
    op.create_index("ix_import_logs_status", "import_logs", ["status"])
    op.create_index("ix_import_logs_file_hash", "import_logs", ["file_hash"])
    op.create_index("ix_import_logs_created_at", "import_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("import_logs")
