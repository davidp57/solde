"""Data migrations, run for real on a SQLite file seeded at the revision before them."""

from pathlib import Path

from sqlalchemy import create_engine, text

from tests.unit.test_schema_drift import run_alembic, upgrade_to


def _execute(db_path: Path, *statements: str) -> None:
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        with engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))
    finally:
        engine.dispose()


def _rows(db_path: Path, query: str) -> list[tuple[object, ...]]:
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        with engine.connect() as conn:
            return [tuple(row) for row in conn.execute(text(query))]
    finally:
        engine.dispose()


def _entry(entry_number: str, *, fy: int | None = None, source: str = "NULL, NULL") -> str:
    fiscal_year = "NULL" if fy is None else str(fy)
    return (
        "INSERT INTO accounting_entries (entry_number, date, account_number, label, "
        "debit, credit, fiscal_year_id, source_type, source_id) "
        f"VALUES ('{entry_number}', '2025-01-01', '512000', 'x', 1, 0, {fiscal_year}, {source})"
    )


# ---------------------------------------------------------------------------
# 0052 — unique entry number (issue #165)
# ---------------------------------------------------------------------------


def test_0052_renumbers_duplicate_entry_numbers_instead_of_failing(tmp_path: Path) -> None:
    """A pre-0052 database may hold duplicates: the container must still start."""
    db_path = tmp_path / "dupes.db"
    upgrade_to(db_path, "0051")
    _execute(
        db_path,
        _entry("000001"),
        _entry("000002"),
        _entry("000002"),
        _entry("000002"),
        _entry("000007"),
        _entry("RUN-1"),
        _entry("RUN-1"),
    )

    upgrade_to(db_path, "0052")

    numbers = [row[0] for row in _rows(db_path, "SELECT entry_number FROM accounting_entries")]
    assert len(numbers) == len(set(numbers)) == 7
    # The first line of each duplicate set keeps its number; the others go past the
    # current maximum, in id order.
    by_id = _rows(db_path, "SELECT id, entry_number FROM accounting_entries ORDER BY id")
    assert [number for _, number in by_id] == [
        "000001",
        "000002",
        "000008",
        "000009",
        "000007",
        "RUN-1",
        "000010",
    ]


def test_0052_leaves_a_clean_database_untouched(tmp_path: Path) -> None:
    db_path = tmp_path / "clean.db"
    upgrade_to(db_path, "0051")
    _execute(db_path, _entry("000001"), _entry("000002"))

    upgrade_to(db_path, "0052")

    assert _rows(db_path, "SELECT entry_number FROM accounting_entries ORDER BY id") == [
        ("000001",),
        ("000002",),
    ]


# ---------------------------------------------------------------------------
# c3d9a1e5f702 — carry-forward entries get a group of their own (issue #197)
# ---------------------------------------------------------------------------


def test_carry_forward_lines_move_to_the_year_they_open(tmp_path: Path) -> None:
    db_path = tmp_path / "ran.db"
    upgrade_to(db_path, "5b8e2d7c1f46")
    _execute(
        db_path,
        "INSERT INTO fiscal_years (id, name, start_date, end_date, status) VALUES "
        "(1, '2024', '2024-08-01', '2025-07-31', 'closed'), "
        "(2, '2025', '2025-08-01', '2026-07-31', 'open')",
        # Closing lines of 2024, in 2024.
        _entry("000001", fy=1, source="'cloture', 1"),
        _entry("000002", fy=1, source="'cloture', 1"),
        # Carry-forward lines of 2025, written with the old key of 2024.
        _entry("000003", fy=2, source="'cloture', 1"),
        _entry("000004", fy=2, source="'cloture', 1"),
        # Anything else stays as it is.
        _entry("000005", fy=2, source="'payment', 1"),
        "UPDATE accounting_entries SET group_key = source_type || ':' || source_id",
    )

    upgrade_to(db_path, "c3d9a1e5f702")

    rows = _rows(
        db_path,
        "SELECT entry_number, source_type, source_id, group_key "
        "FROM accounting_entries ORDER BY entry_number",
    )
    assert rows == [
        ("000001", "cloture", 1, "cloture:1"),
        ("000002", "cloture", 1, "cloture:1"),
        ("000003", "ran", 2, "ran:2"),
        ("000004", "ran", 2, "ran:2"),
        ("000005", "payment", 1, "payment:1"),
    ]

    result = run_alembic(db_path, "downgrade", "5b8e2d7c1f46")
    assert result.returncode == 0, result.stderr
    assert _rows(
        db_path,
        "SELECT entry_number, source_type, source_id, group_key "
        "FROM accounting_entries WHERE entry_number IN ('000003', '000004') "
        "ORDER BY entry_number",
    ) == [("000003", "cloture", 1, "cloture:1"), ("000004", "cloture", 1, "cloture:1")]
