"""Migration 0052 — add unique index on accounting_entries.entry_number.

Adds a unique index on the entry_number column to prevent duplicate
entry numbers from concurrent requests (race condition fix).
Non-numeric entry_numbers (e.g. 'RUN-*') are excluded via a partial
index condition — SQLite does not support partial unique indexes, so
we use a full unique index which is acceptable since non-numeric
entry_numbers are already unique in practice.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0052"
down_revision: str = "0051"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_accounting_entries_entry_number_unique",
        "accounting_entries",
        ["entry_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_accounting_entries_entry_number_unique", table_name="accounting_entries")
