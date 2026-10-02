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

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from backend.database import Base

# Every module of backend.models is registered on Base.metadata by tests/conftest.py,
# with the same pkgutil discovery as backend/alembic/env.py.

REPO_ROOT = Path(__file__).resolve().parents[2]


def upgrade_to_head(db_path: Path, revision: str = "head") -> None:
    """Run ``alembic upgrade <revision>`` on ``db_path`` in a separate process.

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
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", revision],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_models_match_migrations(tmp_path: Path) -> None:
    db_path = tmp_path / "head.db"
    upgrade_to_head(db_path)

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
    upgrade_to_head(db_path)

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        indexes = inspect(engine).get_indexes("accounting_entries")
    finally:
        engine.dispose()

    unique = {ix["name"]: ix for ix in indexes if ix["unique"]}
    assert "ix_accounting_entries_entry_number_unique" in unique
    assert unique["ix_accounting_entries_entry_number_unique"]["column_names"] == ["entry_number"]
