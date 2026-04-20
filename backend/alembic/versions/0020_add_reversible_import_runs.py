"""Migration 0020 — add reversible import runs, operations and effects."""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("comparison_start_date", sa.Date(), nullable=True),
        sa.Column("comparison_end_date", sa.Date(), nullable=True),
        sa.Column("preview_json", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_runs_id", "import_runs", ["id"])
    op.create_index("ix_import_runs_import_type", "import_runs", ["import_type"])
    op.create_index("ix_import_runs_status", "import_runs", ["status"])
    op.create_index("ix_import_runs_file_hash", "import_runs", ["file_hash"])
    op.create_index("ix_import_runs_created_at", "import_runs", ["created_at"])

    op.create_table(
        "import_operations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("operation_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_sheet", sa.String(length=255), nullable=True),
        sa.Column("source_row_numbers_json", sa.Text(), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("diagnostics_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["run_id"], ["import_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_operations_id", "import_operations", ["id"])
    op.create_index("ix_import_operations_run_id", "import_operations", ["run_id"])
    op.create_index("ix_import_operations_operation_type", "import_operations", ["operation_type"])
    op.create_index("ix_import_operations_decision", "import_operations", ["decision"])
    op.create_index("ix_import_operations_status", "import_operations", ["status"])

    op.create_table(
        "import_effects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("entity_reference", sa.String(length=255), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("before_snapshot_json", sa.Text(), nullable=True),
        sa.Column("after_snapshot_json", sa.Text(), nullable=True),
        sa.Column("before_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("after_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["operation_id"], ["import_operations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_effects_id", "import_effects", ["id"])
    op.create_index("ix_import_effects_operation_id", "import_effects", ["operation_id"])
    op.create_index("ix_import_effects_entity_type", "import_effects", ["entity_type"])
    op.create_index("ix_import_effects_entity_id", "import_effects", ["entity_id"])
    op.create_index("ix_import_effects_status", "import_effects", ["status"])


def downgrade() -> None:
    op.drop_table("import_effects")
    op.drop_table("import_operations")
    op.drop_table("import_runs")
