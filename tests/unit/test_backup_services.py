"""Unit tests for backup services.

Tests:
- backup_destination_service: write_rclone_config, test_destination_connection
- backup_restore_service: _do_test_restore on valid/corrupted/empty SQLite files
- backup_scheduler: src_paths construction (BIZ-201 — data/pdfs inclusion)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.backup_destination import BackupDestination
from backend.schemas.backup import BackupConnectionTestResult, BackupRestoreTestResult
from backend.services import backup_destination_service as bds
from backend.services.backup_restore_service import (
    _EXPECTED_TABLES,
    _do_test_restore,
)
from backend.services.backup_restore_service import (
    test_restore as service_test_restore,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dest(
    *,
    name: str = "test-dest",
    dest_type: str = "local",
    rclone_remote_name: str = "myremote",
    rclone_config: str | None = None,
    target_path: str = "/backup",
    enabled: bool = True,
) -> BackupDestination:
    dest = BackupDestination()
    dest.id = 1
    dest.name = name
    dest.type = dest_type
    dest.rclone_remote_name = rclone_remote_name
    dest.rclone_config = rclone_config
    dest.target_path = target_path
    dest.enabled = enabled
    return dest


def _make_valid_db(path: Path) -> None:
    """Create a minimal SQLite file that passes the integrity check."""
    conn = sqlite3.connect(str(path))
    for table in _EXPECTED_TABLES:
        conn.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# write_rclone_config
# ---------------------------------------------------------------------------


class TestBuildRcloneConf:
    def test_local_dest(self) -> None:
        dest = _make_dest(dest_type="local", rclone_remote_name="local-nas")
        content = bds._build_rclone_conf([dest])
        assert "[local-nas]" in content
        assert "type = local" in content

    def test_smb_dest(self) -> None:
        import json

        cfg = json.dumps({"host": "192.168.1.10", "user": "admin", "pass": "secret", "domain": ""})
        dest = _make_dest(dest_type="smb", rclone_remote_name="nas-smb", rclone_config=cfg)
        content = bds._build_rclone_conf([dest])
        assert "[nas-smb]" in content
        assert "type = smb" in content
        assert "host = 192.168.1.10" in content
        assert "user = admin" in content

    def test_onedrive_dest(self) -> None:
        import json

        cfg = json.dumps({"token": '{"access_token":"abc"}', "drive_id": "xyz"})
        dest = _make_dest(dest_type="onedrive", rclone_remote_name="od-perso", rclone_config=cfg)
        content = bds._build_rclone_conf([dest])
        assert "[od-perso]" in content
        assert "type = onedrive" in content

    def test_invalid_json_config_is_handled(self) -> None:
        dest = _make_dest(dest_type="smb", rclone_config="NOT_JSON")
        content = bds._build_rclone_conf([dest])
        # Should not raise; section still created
        assert "[myremote]" in content

    def test_multiple_destinations(self) -> None:
        d1 = _make_dest(dest_type="local", rclone_remote_name="r1")
        d2 = _make_dest(dest_type="local", rclone_remote_name="r2")
        content = bds._build_rclone_conf([d1, d2])
        assert "[r1]" in content
        assert "[r2]" in content

    def test_write_rclone_config(self, tmp_path: Path) -> None:
        dest = _make_dest(dest_type="local", rclone_remote_name="local-bk")
        with patch.object(bds, "_RCLONE_CONF_PATH", tmp_path / "rclone.conf"):
            bds.write_rclone_config([dest])
            conf_path = tmp_path / "rclone.conf"
            assert conf_path.exists()
            text = conf_path.read_text()
            assert "[local-bk]" in text


# ---------------------------------------------------------------------------
# test_destination_connection
# ---------------------------------------------------------------------------


class TestTestDestinationConnection:
    @pytest.mark.asyncio
    async def test_success(self) -> None:
        dest = _make_dest(dest_type="local", rclone_remote_name="r1")

        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"dir1\n", b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
            result = await bds.test_destination_connection(dest)

        assert isinstance(result, BackupConnectionTestResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_failure(self) -> None:
        dest = _make_dest(dest_type="smb", rclone_remote_name="r-fail")

        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Failed to connect"))
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
            result = await bds.test_destination_connection(dest)

        assert isinstance(result, BackupConnectionTestResult)
        assert result.success is False
        assert "connexion" in result.message.lower()

    @pytest.mark.asyncio
    async def test_subprocess_raises(self) -> None:
        dest = _make_dest()

        with patch(
            "asyncio.create_subprocess_exec",
            AsyncMock(side_effect=FileNotFoundError("rclone not found")),
        ):
            result = await bds.test_destination_connection(dest)

        assert result.success is False


# ---------------------------------------------------------------------------
# _do_test_restore / test_restore
# ---------------------------------------------------------------------------


class TestDoTestRestore:
    def test_valid_db(self, tmp_path: Path) -> None:
        db = tmp_path / "valid.db"
        _make_valid_db(db)
        result = _do_test_restore(db)
        assert isinstance(result, BackupRestoreTestResult)
        assert result.ok is True
        assert result.integrity_check == "ok"
        assert result.tables_missing == []

    def test_missing_tables(self, tmp_path: Path) -> None:
        db = tmp_path / "partial.db"
        conn = sqlite3.connect(str(db))
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        result = _do_test_restore(db)
        assert result.ok is False
        # users present, many others missing
        assert "invoices" in result.tables_missing

    def test_not_a_sqlite_file(self, tmp_path: Path) -> None:
        db = tmp_path / "garbage.db"
        db.write_bytes(b"This is not SQLite data at all!")
        result = _do_test_restore(db)
        assert result.ok is False

    def test_empty_file(self, tmp_path: Path) -> None:
        db = tmp_path / "empty.db"
        db.write_bytes(b"")
        result = _do_test_restore(db)
        assert result.ok is False


class TestTestRestore:
    @pytest.mark.asyncio
    async def test_nonexistent_path(self, tmp_path: Path) -> None:
        result = await service_test_restore(str(tmp_path / "does_not_exist.db"))
        assert result.ok is False
        assert result.error_code == "BACKUP_FILE_NOT_FOUND"
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_valid_db(self, tmp_path: Path) -> None:
        db = tmp_path / "valid.db"
        _make_valid_db(db)
        result = await service_test_restore(str(db))
        assert result.ok is True


# ---------------------------------------------------------------------------
# backup_scheduler — src_paths construction (BIZ-201)
# ---------------------------------------------------------------------------


def _make_scheduler_patches(
    fake_backup: Path,
    dest: BackupDestination,
    sync_side_effect,
) -> list:
    """Return a list of patch objects for _run_backup_job_inner dependencies."""
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [dest]
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)
    get_session_mock = MagicMock(return_value=mock_session_ctx)

    return [
        patch("backend.services.backup_service.create_backup", AsyncMock(return_value=fake_backup)),
        patch(
            "backend.services.backup_restore_service.test_restore",
            AsyncMock(return_value=MagicMock(ok=True)),
        ),
        patch("backend.database.get_session", get_session_mock),
        patch("backend.services.backup_destination_service.refresh_onedrive_tokens", AsyncMock()),
        patch("backend.services.backup_destination_service.write_rclone_config", MagicMock()),
        patch(
            "backend.services.backup_destination_service.sync_destination",
            side_effect=sync_side_effect,
        ),
        patch("backend.services.backup_scheduler._update_run_status", AsyncMock()),
    ]


def _make_dest_obj(name: str = "local-dest") -> BackupDestination:
    dest = BackupDestination()
    dest.id = 1
    dest.name = name
    dest.type = "local"
    dest.rclone_remote_name = "local"
    dest.rclone_config = None
    dest.target_path = "/backup"
    dest.enabled = True
    return dest


class TestBackupJobPdfsInclusion:
    """BIZ-201: data/pdfs must always be included in the backup src_paths."""

    @pytest.mark.asyncio
    async def test_pdfs_included_snapshot_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """data/pdfs is included in src_paths in snapshot (single-file) mode."""
        (tmp_path / "data" / "pdfs").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        fake_backup = tmp_path / "solde_backup_20260101_120000.db"
        fake_backup.write_bytes(b"fake")
        dest = _make_dest_obj()
        captured: list[list[str]] = []

        async def _fake_sync(dest, src_paths, run_ts, on_progress=None):
            captured.append(list(src_paths))

        from backend.services import backup_scheduler as sched

        patches = _make_scheduler_patches(fake_backup, dest, _fake_sync)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
            await sched._run_backup_job_inner(
                db_path="data/solde.db",
                backup_dir="data/backups",
                include_uploads=False,
                include_all_backups=False,
                notify_on_failure=False,
            )

        expected_pdfs = str((tmp_path / "data" / "pdfs").resolve())
        assert len(captured) == 1
        assert expected_pdfs in captured[0], f"data/pdfs absent de src_paths: {captured[0]}"

    @pytest.mark.asyncio
    async def test_pdfs_included_full_backup_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """data/pdfs is included in src_paths in full-backup (include_all_backups) mode."""
        (tmp_path / "data" / "pdfs").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        fake_backup = tmp_path / "solde_backup_20260101_120000.db"
        fake_backup.write_bytes(b"fake")
        dest = _make_dest_obj()
        captured: list[list[str]] = []

        async def _fake_sync(dest, src_paths, run_ts, on_progress=None):
            captured.append(list(src_paths))

        from backend.services import backup_scheduler as sched

        patches = _make_scheduler_patches(fake_backup, dest, _fake_sync)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
            await sched._run_backup_job_inner(
                db_path="data/solde.db",
                backup_dir="data/backups",
                include_uploads=False,
                include_all_backups=True,
                notify_on_failure=False,
            )

        expected_pdfs = str((tmp_path / "data" / "pdfs").resolve())
        assert len(captured) == 1
        assert expected_pdfs in captured[0], f"data/pdfs absent de src_paths: {captured[0]}"

    @pytest.mark.asyncio
    async def test_pdfs_skipped_when_directory_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """data/pdfs is NOT added to src_paths when the directory does not exist."""
        # data/pdfs directory intentionally NOT created
        monkeypatch.chdir(tmp_path)

        fake_backup = tmp_path / "solde_backup_20260101_120000.db"
        fake_backup.write_bytes(b"fake")
        dest = _make_dest_obj()
        captured: list[list[str]] = []

        async def _fake_sync(dest, src_paths, run_ts, on_progress=None):
            captured.append(list(src_paths))

        from backend.services import backup_scheduler as sched

        patches = _make_scheduler_patches(fake_backup, dest, _fake_sync)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
            await sched._run_backup_job_inner(
                db_path="data/solde.db",
                backup_dir="data/backups",
                include_uploads=False,
                include_all_backups=False,
                notify_on_failure=False,
            )

        expected_pdfs = str((tmp_path / "data" / "pdfs").resolve())
        assert len(captured) == 1
        assert expected_pdfs not in captured[0], (
            f"data/pdfs ne devrait pas être dans src_paths: {captured[0]}"
        )
