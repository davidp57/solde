"""give the carry-forward entries a group of their own

Opening a fiscal year wrote its report-à-nouveau entries as ``cloture`` entries
keyed by the year being closed (``source_id`` = closed year, ``group_key`` =
``cloture:<closed year>``) — the very key of that year's closing entries. The
grouped journal then mixed two fiscal years in one group (issue #197).

The carry-forward lines are the ``cloture`` lines that sit in another fiscal year
than their ``source_id``: closing lines always belong to the year they close.
They become ``ran`` lines keyed by the year they open.

Revision ID: c3d9a1e5f702
Revises: 5b8e2d7c1f46
Create Date: 2026-11-09 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d9a1e5f702"
down_revision: str | None = "5b8e2d7c1f46"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE accounting_entries
        SET source_type = 'ran',
            source_id = fiscal_year_id,
            group_key = 'ran:' || fiscal_year_id
        WHERE source_type = 'cloture'
          AND fiscal_year_id IS NOT NULL
          AND source_id IS NOT NULL
          AND fiscal_year_id != source_id
        """
    )


def downgrade() -> None:
    # Back to the old key: the year closed just before the one the lines open.
    op.execute(
        """
        UPDATE accounting_entries
        SET source_type = 'cloture',
            source_id = (
                SELECT prev.id FROM fiscal_years AS prev
                JOIN fiscal_years AS opened ON opened.id = accounting_entries.fiscal_year_id
                WHERE prev.end_date < opened.start_date
                ORDER BY prev.end_date DESC
                LIMIT 1
            )
        WHERE source_type = 'ran'
        """
    )
    op.execute(
        """
        UPDATE accounting_entries
        SET group_key = 'cloture:' || source_id
        WHERE source_type = 'cloture' AND group_key LIKE 'ran:%' AND source_id IS NOT NULL
        """
    )
