"""Guard: the ORM models and the Alembic migrations must describe the same schema.

The rest of the suite builds its schema with ``Base.metadata.create_all``, i.e. from
the models, so it cannot see what ``alembic upgrade head`` really produces. This test
upgrades a fresh SQLite file to ``head`` and requires ``compare_metadata`` to be empty:
any drift would otherwise be swept into the next ``alembic revision --autogenerate``.
"""

import os
import subprocess
import sys
from pathlib import Path
from pprint import pformat

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from backend.database import Base

# Every module of backend.models is registered on Base.metadata by tests/conftest.py,
# with the same pkgutil discovery as backend/alembic/env.py.

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_alembic(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run ``alembic <args>`` on ``db_path`` in a separate process.

    A subprocess keeps env.py's ``asyncio.run`` off the test event loop and its
    cached settings away from the test process. ``PYTHONPATH`` pins the code of
    this checkout, not an editable install from another one.
    """
    env = {
        **os.environ,
        "DEBUG": "true",
        "DATABASE_URL": f"sqlite+aiosqlite:///{db_path.as_posix()}",
        "PYTHONPATH": str(REPO_ROOT),
    }
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def upgrade_to(db_path: Path, revision: str = "head") -> None:
    result = run_alembic(db_path, "upgrade", revision)
    assert result.returncode == 0, result.stderr


def unique_indexes(db_path: Path, table: str) -> dict[str, list[str | None]]:
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        indexes = inspect(engine).get_indexes(table)
    finally:
        engine.dispose()
    return {str(ix["name"]): list(ix["column_names"]) for ix in indexes if ix["unique"]}


def test_models_match_migrations(tmp_path: Path) -> None:
    db_path = tmp_path / "head.db"
    upgrade_to(db_path)

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        with engine.connect() as conn:
            context = MigrationContext.configure(conn, opts={"compare_type": True})
            diff = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()

    assert not diff, (
        f"{len(diff)} drift(s) between backend/models and the migrations at head:\n"
        f"{pformat(diff, width=100)}"
    )


def test_entry_number_unique_index_survives_upgrade(tmp_path: Path) -> None:
    """The anti-duplicate guard from migration 0052 must still exist at head."""
    db_path = tmp_path / "head.db"
    upgrade_to(db_path)

    assert unique_indexes(db_path, "accounting_entries")[
        "ix_accounting_entries_entry_number_unique"
    ] == ["entry_number"]


def test_fiscal_year_name_and_rule_trigger_are_unique_at_head(tmp_path: Path) -> None:
    """The database itself rejects a second fiscal year name or rule trigger.

    Migrations 0007 and 0009 declared these columns ``unique=True``: the guard is a
    table-level UNIQUE constraint, next to a plain index of the same column.
    """
    db_path = tmp_path / "head.db"
    upgrade_to(db_path)

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        constraints = {
            table: [uc["column_names"] for uc in inspect(engine).get_unique_constraints(table)]
            for table in ("fiscal_years", "accounting_rules")
        }
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO fiscal_years (name, start_date, end_date, status) "
                    "VALUES ('2025', '2025-08-01', '2026-07-31', 'open')"
                )
            )
        with pytest.raises(IntegrityError), engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO fiscal_years (name, start_date, end_date, status) "
                    "VALUES ('2025', '2026-08-01', '2027-07-31', 'open')"
                )
            )
        rule = (
            "INSERT INTO accounting_rules (name, trigger_type, is_active, priority) "
            "VALUES ('Frais bancaires', 'bank_fees', 1, 10)"
        )
        with engine.begin() as conn:
            conn.execute(text(rule))
        with pytest.raises(IntegrityError), engine.begin() as conn:
            conn.execute(text(rule))
    finally:
        engine.dispose()

    assert constraints == {"fiscal_years": [["name"]], "accounting_rules": [["trigger_type"]]}
