"""Migration 0052 — add unique index on accounting_entries.entry_number.

Adds a unique index on the entry_number column to prevent duplicate
entry numbers from concurrent requests (race condition fix).

The index cannot be created over existing duplicates, and a database from before
this migration may hold some: opening a fiscal year with several balances used to
give every carry-forward line the same number. A failed migration stops the
container at startup, so duplicates are renumbered first — the first line of each
set (lowest id) keeps its number, the others take fresh numbers past the current
numeric maximum. ``group_key`` and ``source_type``/``source_id`` do not depend on
``entry_number``, so every line stays attached to its document.
"""

import logging
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0052"
down_revision: str = "0051"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

logger = logging.getLogger("alembic.runtime.migration")


def _renumber_duplicates() -> None:
    conn = op.get_bind()
    duplicates = conn.execute(
        sa.text(
            "SELECT id, entry_number FROM accounting_entries "
            "WHERE entry_number IN ("
            "  SELECT entry_number FROM accounting_entries "
            "  GROUP BY entry_number HAVING COUNT(*) > 1"
            ") ORDER BY id"
        )
    ).fetchall()
    if not duplicates:
        return

    current_max = conn.execute(
        sa.text(
            "SELECT MAX(entry_number) FROM accounting_entries "
            "WHERE entry_number GLOB '[0-9][0-9][0-9][0-9][0-9][0-9]'"
        )
    ).scalar()
    next_number = 1 if current_max is None else int(current_max) + 1

    kept: set[str] = set()
    for entry_id, entry_number in duplicates:
        if entry_number not in kept:
            kept.add(entry_number)
            continue
        new_number = f"{next_number:06d}"
        next_number += 1
        conn.execute(
            sa.text("UPDATE accounting_entries SET entry_number = :number WHERE id = :id"),
            {"number": new_number, "id": entry_id},
        )
        logger.warning(
            "Duplicate entry number %s: entry id %s renumbered %s",
            entry_number,
            entry_id,
            new_number,
        )


def upgrade() -> None:
    _renumber_duplicates()
    op.create_index(
        "ix_accounting_entries_entry_number_unique",
        "accounting_entries",
        ["entry_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_accounting_entries_entry_number_unique", table_name="accounting_entries")
