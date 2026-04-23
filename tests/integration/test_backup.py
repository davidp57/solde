"""Tests for SQLite backup service and endpoint (BL-069)."""

from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Unit tests — backup_service
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_backup_produces_file(tmp_path: Path) -> None:
    """create_backup must produce a .db file in the target directory."""
    # Create a real SQLite source DB
    import aiosqlite

    src_db = tmp_path / "source.db"
    async with aiosqlite.connect(str(src_db)) as db:
        await db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        await db.execute("INSERT INTO t VALUES (1)")
        await db.commit()

    from backend.services.backup_service import create_backup

    backup_dir = tmp_path / "backups"
    result = await create_backup(
        db_path=str(src_db),
        backup_dir=str(backup_dir),
        max_backups=5,
    )

    assert result.exists()
    assert result.suffix == ".db"
    assert backup_dir.exists()

    # Verify the backup is a valid SQLite DB with the same data
    async with aiosqlite.connect(str(result)) as db:
        cursor = await db.execute("SELECT id FROM t")
        rows = await cursor.fetchall()
        assert rows == [(1,)]


@pytest.mark.asyncio
async def test_backup_rotation_keeps_max_files(tmp_path: Path) -> None:
    """Older backups beyond max_backups must be deleted."""
    import aiosqlite

    src_db = tmp_path / "source.db"
    async with aiosqlite.connect(str(src_db)) as db:
        await db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        await db.commit()

    from unittest.mock import patch as sync_patch

    from backend.services.backup_service import create_backup

    backup_dir = tmp_path / "backups"

    # Create 6 backups with distinct timestamps by mocking datetime
    paths = []
    for i in range(6):
        fake_ts = f"2026042{i}_12000{i}"
        with sync_patch("backend.services.backup_service.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = fake_ts
            mock_dt.side_effect = None
            p = await create_backup(
                db_path=str(src_db),
                backup_dir=str(backup_dir),
                max_backups=3,
            )
            paths.append(p)

    remaining = list(backup_dir.glob("*.db"))
    assert len(remaining) == 3

    # The 3 most recent should be kept
    remaining_names = {f.name for f in remaining}
    for p in paths[-3:]:
        assert p.name in remaining_names


@pytest.mark.asyncio
async def test_backup_filename_contains_timestamp(tmp_path: Path) -> None:
    """Backup filename must contain a sortable timestamp."""
    import aiosqlite

    src_db = tmp_path / "source.db"
    async with aiosqlite.connect(str(src_db)) as db:
        await db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        await db.commit()

    from backend.services.backup_service import create_backup

    result = await create_backup(
        db_path=str(src_db),
        backup_dir=str(tmp_path / "backups"),
        max_backups=5,
    )

    # Format: solde_backup_YYYYMMDD_HHMMSS.db
    assert result.name.startswith("solde_backup_")
    assert len(result.stem) > len("solde_backup_")


# ---------------------------------------------------------------------------
# Integration tests — API endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backup_endpoint_requires_admin(
    client: AsyncClient,
    secretaire_auth_headers: dict[str, str],
) -> None:
    """Non-admin users must get 403 on the backup endpoint."""
    resp = await client.post("/api/settings/backup", headers=secretaire_auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_backup_endpoint_returns_file(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
) -> None:
    """POST /api/settings/backup must return the backup as a downloadable file."""
    import aiosqlite

    # Create a temp SQLite DB as the "app database"
    src_db = tmp_path / "test_solde.db"
    async with aiosqlite.connect(str(src_db)) as db:
        await db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        await db.execute("INSERT INTO t VALUES (42)")
        await db.commit()

    backup_dir = tmp_path / "backups"

    with (
        patch("backend.routers.settings._get_db_path", return_value=str(src_db)),
        patch("backend.routers.settings._get_backup_dir", return_value=str(backup_dir)),
    ):
        resp = await client.post("/api/settings/backup", headers=auth_headers)

    assert resp.status_code == 200
    assert "application/octet-stream" in resp.headers["content-type"]
    assert "attachment" in resp.headers.get("content-disposition", "")

    # Verify the returned bytes are a valid SQLite database
    downloaded = tmp_path / "downloaded.db"
    downloaded.write_bytes(resp.content)
    async with aiosqlite.connect(str(downloaded)) as db:
        cursor = await db.execute("SELECT id FROM t")
        rows = await cursor.fetchall()
        assert rows == [(42,)]


@pytest.mark.asyncio
async def test_backup_endpoint_creates_backup_on_disk(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
) -> None:
    """POST /api/settings/backup must also store the backup in the backup dir."""
    import aiosqlite

    src_db = tmp_path / "test_solde.db"
    async with aiosqlite.connect(str(src_db)) as db:
        await db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        await db.commit()

    backup_dir = tmp_path / "backups"

    with (
        patch("backend.routers.settings._get_db_path", return_value=str(src_db)),
        patch("backend.routers.settings._get_backup_dir", return_value=str(backup_dir)),
    ):
        await client.post("/api/settings/backup", headers=auth_headers)

    backups = list(backup_dir.glob("*.db"))
    assert len(backups) == 1
