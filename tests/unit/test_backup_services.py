"""Unit tests for backup services.

Tests:
- backup_destination_service: write_rclone_config, test_destination_connection
- backup_restore_service: _do_test_restore on valid/corrupted/empty SQLite files
- backup_scheduler: asset mirroring (TEC-209) + remote retention (TEC-208)
"""

from __future__ import annotations

import sqlite3
from contextlib import ExitStack
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
# backup_scheduler — asset mirror + snapshot (TEC-209)
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
        patch(
            "backend.services.backup_destination_service.prune_remote_backups",
            AsyncMock(return_value=0),
        ),
        patch("backend.services.backup_scheduler._update_run_status", AsyncMock()),
    ]


class TestBackupJobAssetMirror:
    """TEC-209: PDFs/uploads are mirrored to stable folders, not bundled into the
    timestamped snapshot."""

    @staticmethod
    def _mirror_subdirs(mirror_mock: AsyncMock) -> list[str]:
        return [call.args[2] for call in mirror_mock.call_args_list]

    @pytest.mark.asyncio
    async def test_pdfs_mirrored_not_in_snapshot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """data/pdfs is excluded from the snapshot and mirrored to the stable folder."""
        (tmp_path / "data" / "pdfs").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        fake_backup = tmp_path / "solde_backup_20260101_120000.db"
        fake_backup.write_bytes(b"fake")
        dest = _make_dest(name="local-dest", rclone_remote_name="local")
        captured: list[list[str]] = []

        async def _fake_sync(dest, src_paths, run_ts, on_progress=None):
            captured.append(list(src_paths))

        mirror_mock = AsyncMock(return_value=1)
        from backend.services import backup_scheduler as sched

        patches = _make_scheduler_patches(fake_backup, dest, _fake_sync)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            stack.enter_context(
                patch(
                    "backend.services.backup_destination_service.mirror_dir_incremental",
                    mirror_mock,
                )
            )
            await sched._run_backup_job_inner(
                db_path="data/solde.db",
                backup_dir="data/backups",
                include_uploads=False,
                include_all_backups=False,
                notify_on_failure=False,
            )

        expected_pdfs = str((tmp_path / "data" / "pdfs").resolve())
        assert len(captured) == 1
        assert expected_pdfs not in captured[0]  # no longer bundled in the snapshot
        mirrored = [call.args for call in mirror_mock.call_args_list]
        assert any(args[1] == expected_pdfs and args[2] == "pdfs" for args in mirrored)

    @pytest.mark.asyncio
    async def test_pdfs_mirrored_in_full_backup_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PDFs are still mirrored (not snapshotted) in include_all_backups mode."""
        (tmp_path / "data" / "pdfs").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        fake_backup = tmp_path / "solde_backup_20260101_120000.db"
        fake_backup.write_bytes(b"fake")
        dest = _make_dest(name="local-dest", rclone_remote_name="local")
        captured: list[list[str]] = []

        async def _fake_sync(dest, src_paths, run_ts, on_progress=None):
            captured.append(list(src_paths))

        mirror_mock = AsyncMock(return_value=1)
        from backend.services import backup_scheduler as sched

        patches = _make_scheduler_patches(fake_backup, dest, _fake_sync)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            stack.enter_context(
                patch(
                    "backend.services.backup_destination_service.mirror_dir_incremental",
                    mirror_mock,
                )
            )
            await sched._run_backup_job_inner(
                db_path="data/solde.db",
                backup_dir="data/backups",
                include_uploads=False,
                include_all_backups=True,
                notify_on_failure=False,
            )

        expected_pdfs = str((tmp_path / "data" / "pdfs").resolve())
        assert expected_pdfs not in captured[0]
        assert "pdfs" in self._mirror_subdirs(mirror_mock)

    @pytest.mark.asyncio
    async def test_pdfs_not_mirrored_when_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No mirror call for pdfs when data/pdfs does not exist."""
        monkeypatch.chdir(tmp_path)  # data/pdfs intentionally not created

        fake_backup = tmp_path / "solde_backup_20260101_120000.db"
        fake_backup.write_bytes(b"fake")
        dest = _make_dest(name="local-dest", rclone_remote_name="local")

        async def _fake_sync(dest, src_paths, run_ts, on_progress=None):
            pass

        mirror_mock = AsyncMock(return_value=0)
        from backend.services import backup_scheduler as sched

        patches = _make_scheduler_patches(fake_backup, dest, _fake_sync)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            stack.enter_context(
                patch(
                    "backend.services.backup_destination_service.mirror_dir_incremental",
                    mirror_mock,
                )
            )
            await sched._run_backup_job_inner(
                db_path="data/solde.db",
                backup_dir="data/backups",
                include_uploads=False,
                include_all_backups=False,
                notify_on_failure=False,
            )

        assert "pdfs" not in self._mirror_subdirs(mirror_mock)

    @pytest.mark.asyncio
    async def test_uploads_mirrored_when_included(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """data/uploads is mirrored (not snapshotted) when include_uploads is True."""
        (tmp_path / "data" / "uploads").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        fake_backup = tmp_path / "solde_backup_20260101_120000.db"
        fake_backup.write_bytes(b"fake")
        dest = _make_dest(name="local-dest", rclone_remote_name="local")
        captured: list[list[str]] = []

        async def _fake_sync(dest, src_paths, run_ts, on_progress=None):
            captured.append(list(src_paths))

        mirror_mock = AsyncMock(return_value=0)
        from backend.services import backup_scheduler as sched

        patches = _make_scheduler_patches(fake_backup, dest, _fake_sync)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            stack.enter_context(
                patch(
                    "backend.services.backup_destination_service.mirror_dir_incremental",
                    mirror_mock,
                )
            )
            await sched._run_backup_job_inner(
                db_path="data/solde.db",
                backup_dir="data/backups",
                include_uploads=True,
                include_all_backups=False,
                notify_on_failure=False,
            )

        expected_uploads = str((tmp_path / "data" / "uploads").resolve())
        assert expected_uploads not in captured[0]
        mirrored = [call.args for call in mirror_mock.call_args_list]
        assert any(args[1] == expected_uploads and args[2] == "uploads" for args in mirrored)


# ---------------------------------------------------------------------------
# prune_remote_backups (TEC-208 — remote retention)
# ---------------------------------------------------------------------------


def _onedrive_config() -> str:
    import json

    return json.dumps({"drive_id": "d1", "token": json.dumps({"access_token": "tok"})})


class TestPruneRemoteBackups:
    @pytest.mark.asyncio
    async def test_onedrive_keeps_recent_and_ignores_mirror(self) -> None:
        dest = _make_dest(
            dest_type="onedrive", target_path="backups", rclone_config=_onedrive_config()
        )
        snaps = [f"2026-06-{d:02d}T02-00-00" for d in range(1, 8)]  # 7 snapshots
        children = [{"id": n, "name": n, "folder": {}} for n in snaps]
        children += [
            {"id": "pdfs", "name": "pdfs", "folder": {}},  # stable mirror — never pruned
            {"id": "f1", "name": "readme.txt"},  # a file — ignored
        ]
        deleted: list[str] = []

        def _del(client: object, token: str, drive: str, item_id: str) -> None:
            deleted.append(item_id)

        with (
            patch.object(bds, "_graph_list_children", AsyncMock(return_value=children)),
            patch.object(bds, "_graph_delete_item", AsyncMock(side_effect=_del)),
        ):
            n = await bds.prune_remote_backups(dest, keep=5)

        assert n == 2
        assert deleted == ["2026-06-01T02-00-00", "2026-06-02T02-00-00"]

    @pytest.mark.asyncio
    async def test_onedrive_noop_when_at_or_below_keep(self) -> None:
        dest = _make_dest(
            dest_type="onedrive", target_path="backups", rclone_config=_onedrive_config()
        )
        children = [
            {"id": f"s{d}", "name": f"2026-06-0{d}T02-00-00", "folder": {}} for d in range(1, 4)
        ]
        del_mock = AsyncMock()
        with (
            patch.object(bds, "_graph_list_children", AsyncMock(return_value=children)),
            patch.object(bds, "_graph_delete_item", del_mock),
        ):
            n = await bds.prune_remote_backups(dest, keep=5)

        assert n == 0
        del_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_rclone_prunes_oldest_and_ignores_mirror(self) -> None:
        dest = _make_dest(dest_type="smb", rclone_remote_name="smb", target_path="backups")
        calls: list[list[str]] = []

        def _run(cmd: list[str]) -> str:
            calls.append(cmd)
            if cmd[1] == "lsf":
                return "".join(f"2026-06-0{d}T02-00-00/\n" for d in range(1, 8)) + "pdfs/\n"
            return ""

        with patch.object(bds, "_run_rclone", AsyncMock(side_effect=_run)):
            n = await bds.prune_remote_backups(dest, keep=5)

        assert n == 2
        purges = [c for c in calls if c[1] == "purge"]
        assert len(purges) == 2
        assert all("pdfs" not in c[2] for c in purges)

    @pytest.mark.asyncio
    async def test_keep_must_be_positive(self) -> None:
        dest = _make_dest(dest_type="smb")
        with pytest.raises(ValueError):
            await bds.prune_remote_backups(dest, keep=0)


# ---------------------------------------------------------------------------
# BIZ-216 — mirror only non-regenerable PDFs (archived invoices)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_archived_pdf_relpaths_only_archived(db_session) -> None:
    from datetime import date
    from decimal import Decimal

    from backend.models.contact import Contact, ContactType
    from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType

    contact = Contact(type=ContactType.CLIENT, nom="X")
    db_session.add(contact)
    await db_session.flush()

    def _inv(number: str, status: InvoiceStatus, pdf_path: str | None) -> Invoice:
        return Invoice(
            number=number,
            type=InvoiceType.CLIENT,
            contact_id=contact.id,
            date=date(2025, 1, 1),
            total_amount=Decimal("10"),
            paid_amount=Decimal("0"),
            status=status,
            pdf_path=pdf_path,
        )

    db_session.add_all(
        [
            _inv("A-1", InvoiceStatus.ARCHIVED, "data/pdfs/facture_A-1.pdf"),
            _inv("S-1", InvoiceStatus.SENT, "data/pdfs/facture_S-1.pdf"),
            _inv("A-2", InvoiceStatus.ARCHIVED, None),
        ]
    )
    await db_session.commit()

    result = await bds.archived_pdf_relpaths(db_session)
    assert result == {"facture_A-1.pdf"}


@pytest.mark.asyncio
async def test_mirror_rclone_filters_via_files_from(tmp_path: Path) -> None:
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    (pdfs / "facture_A.pdf").write_bytes(b"A")
    (pdfs / "facture_B.pdf").write_bytes(b"B")
    dest = _make_dest(dest_type="local", rclone_remote_name="local")

    captured: dict[str, object] = {}

    async def _fake_rclone(cmd: list[str]) -> None:
        captured["cmd"] = cmd
        idx = cmd.index("--files-from")
        captured["list"] = Path(cmd[idx + 1]).read_text(encoding="utf-8")

    with patch.object(bds, "_run_rclone", side_effect=_fake_rclone):
        await bds.mirror_dir_incremental(
            dest, str(pdfs), "pdfs", allowed_relpaths={"facture_A.pdf"}
        )

    assert "--files-from" in captured["cmd"]  # type: ignore[operator]
    assert captured["list"] == "facture_A.pdf"


@pytest.mark.asyncio
async def test_mirror_rclone_no_filter_without_allowlist(tmp_path: Path) -> None:
    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    (pdfs / "facture_A.pdf").write_bytes(b"A")
    dest = _make_dest(dest_type="local", rclone_remote_name="local")

    captured: dict[str, object] = {}

    async def _fake_rclone(cmd: list[str]) -> None:
        captured["cmd"] = cmd

    with patch.object(bds, "_run_rclone", side_effect=_fake_rclone):
        await bds.mirror_dir_incremental(dest, str(pdfs), "pdfs")

    assert "--files-from" not in captured["cmd"]  # type: ignore[operator]


# ---------------------------------------------------------------------------
# OneDrive children listing — item-id addressing + paging
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(
        self,
        payload: dict[str, object],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload

    def json(self) -> dict[str, object]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"unexpected HTTP {self.status_code}")


class _FakeGraphClient:
    """Minimal httpx.AsyncClient stand-in returning canned Graph responses."""

    def __init__(self, routes: dict[str, dict[str, object]]) -> None:
        self._routes = routes
        self.calls: list[str] = []

    async def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append(url)
        payload = self._routes.get(url)
        if payload is None:
            return _FakeResponse({}, status_code=404)
        return _FakeResponse(payload)


_BASE = bds._GRAPH_BASE
_CHILDREN_Q = f"?$top={bds._GRAPH_PAGE_SIZE}&$select={bds._GRAPH_CHILD_FIELDS}"


class TestGraphListChildren:
    @pytest.mark.asyncio
    async def test_follows_next_link_across_pages(self) -> None:
        """A folder larger than one page is listed in full, addressed by item id."""
        page2 = f"{_BASE}/drives/d1/items/folder1/children?$skiptoken=abc"
        routes = {
            f"{_BASE}/drives/d1/root:/backups/pdfs": {"id": "folder1"},
            f"{_BASE}/drives/d1/items/folder1/children{_CHILDREN_Q}": {
                "value": [{"id": "a", "name": "a.pdf", "size": 1}],
                "@odata.nextLink": page2,
            },
            page2: {"value": [{"id": "b", "name": "b.pdf", "size": 2}]},
        }
        client = _FakeGraphClient(routes)

        items = await bds._graph_list_children(client, "tok", "d1", "backups/pdfs")  # type: ignore[arg-type]

        assert [i["name"] for i in items] == ["a.pdf", "b.pdf"]
        # The children endpoint is never addressed by path — that is what made
        # Graph reject its own nextLink with a 400.
        children_calls = [c for c in client.calls if "/children" in c]
        assert children_calls and all("root:/" not in c for c in children_calls)

    @pytest.mark.asyncio
    async def test_missing_folder_returns_empty(self) -> None:
        client = _FakeGraphClient({})

        items = await bds._graph_list_children(client, "tok", "d1", "backups/pdfs")  # type: ignore[arg-type]

        assert items == []
        assert not [c for c in client.calls if "/children" in c]

    @pytest.mark.asyncio
    async def test_root_folder_uses_root_endpoint(self) -> None:
        routes = {
            f"{_BASE}/drives/d1/root": {"id": "rootid"},
            f"{_BASE}/drives/d1/items/rootid/children{_CHILDREN_Q}": {
                "value": [{"id": "x", "name": "x.pdf", "size": 3}]
            },
        }
        client = _FakeGraphClient(routes)

        items = await bds._graph_list_children(client, "tok", "d1", "")  # type: ignore[arg-type]

        assert [i["name"] for i in items] == ["x.pdf"]


class TestGraphListFiles:
    @pytest.mark.asyncio
    async def test_walks_subfolders_by_id_and_pages(self) -> None:
        page2 = f"{_BASE}/drives/d1/items/root1/children?$skiptoken=xyz"
        routes = {
            f"{_BASE}/drives/d1/root:/backups/pdfs": {"id": "root1"},
            f"{_BASE}/drives/d1/items/root1/children{_CHILDREN_Q}": {
                "value": [{"id": "f1", "name": "facture_A.pdf", "size": 10}],
                "@odata.nextLink": page2,
            },
            page2: {"value": [{"id": "sub1", "name": "2025", "folder": {}}]},
            f"{_BASE}/drives/d1/items/sub1/children{_CHILDREN_Q}": {
                "value": [{"id": "f2", "name": "facture_B.pdf", "size": 20}]
            },
        }
        client = _FakeGraphClient(routes)

        files = await bds._graph_list_files(client, "tok", "d1", "backups/pdfs")  # type: ignore[arg-type]

        assert files == {"facture_A.pdf": 10, "2025/facture_B.pdf": 20}
        # Sub-folder walked through its id, not through a rebuilt path.
        assert f"{_BASE}/drives/d1/items/sub1/children{_CHILDREN_Q}" in client.calls

    @pytest.mark.asyncio
    async def test_absent_mirror_folder_yields_empty_map(self) -> None:
        client = _FakeGraphClient({})

        files = await bds._graph_list_files(client, "tok", "d1", "backups/pdfs")  # type: ignore[arg-type]

        assert files == {}


class TestBackupJobFailureMessage:
    """A destination failure says which stage broke, without the httpx trailer."""

    @pytest.mark.asyncio
    async def test_mirror_failure_names_the_stage(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "data" / "pdfs").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        fake_backup = tmp_path / "solde_backup_20260101_120000.db"
        fake_backup.write_bytes(b"fake")
        dest = _make_dest(name="onedrive", rclone_remote_name="od")

        async def _fake_sync(dest, src_paths, run_ts, on_progress=None):
            return None

        boom = RuntimeError(
            "Client error '400 Bad Request' for url 'https://graph/children'\n"
            "For more information check: https://developer.mozilla.org/x"
        )
        status_mock = AsyncMock()
        from backend.services import backup_scheduler as sched

        patches = _make_scheduler_patches(fake_backup, dest, _fake_sync)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            stack.enter_context(
                patch(
                    "backend.services.backup_destination_service.mirror_dir_incremental",
                    AsyncMock(side_effect=boom),
                )
            )
            stack.enter_context(patch.object(sched, "_update_run_status", status_mock))
            await sched._run_backup_job_inner(
                db_path="data/solde.db",
                backup_dir="data/backups",
                include_uploads=False,
                include_all_backups=False,
                notify_on_failure=False,
            )

        success, error = status_mock.call_args.args
        assert success is False
        assert error is not None
        assert "miroir des PDF" in error
        assert "onedrive" in error
        assert "For more information check" not in error


def test_describe_error_strips_httpx_trailer() -> None:
    from backend.services.backup_scheduler import _describe_error

    exc = RuntimeError("boom\nFor more information check: https://developer.mozilla.org/x")
    assert _describe_error(exc) == "boom"


def test_describe_error_collapses_whitespace() -> None:
    from backend.services.backup_scheduler import _describe_error

    assert _describe_error(RuntimeError("a\n  b\tc")) == "a b c"


# ---------------------------------------------------------------------------
# Graph retry — throttling (429) and transient server errors
# ---------------------------------------------------------------------------


class _SequenceClient:
    """Returns canned responses in order, recording the requests made."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.requests: list[tuple[str, str]] = []

    async def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        self.requests.append((method, url))
        return self._responses.pop(0) if self._responses else _FakeResponse({})


class TestGraphRequestRetry:
    @staticmethod
    def _sleep_spy() -> tuple[AsyncMock, list[float]]:
        waits: list[float] = []

        async def _sleep(seconds: float) -> None:
            waits.append(seconds)

        return AsyncMock(side_effect=_sleep), waits

    @pytest.mark.asyncio
    async def test_retries_throttling_then_succeeds(self) -> None:
        client = _SequenceClient(
            [
                _FakeResponse({}, status_code=429, headers={"Retry-After": "7"}),
                _FakeResponse({"ok": True}),
            ]
        )
        sleep_mock, waits = self._sleep_spy()

        with patch.object(bds.asyncio, "sleep", sleep_mock):
            resp = await bds._graph_request(client, "GET", "https://graph/x")  # type: ignore[arg-type]

        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        assert waits == [7.0]  # honours Retry-After rather than the backoff
        assert len(client.requests) == 2

    @pytest.mark.asyncio
    async def test_gives_up_after_max_retries_with_exponential_backoff(self) -> None:
        client = _SequenceClient([_FakeResponse({}, status_code=503) for _ in range(6)])
        sleep_mock, waits = self._sleep_spy()

        with patch.object(bds.asyncio, "sleep", sleep_mock):
            resp = await bds._graph_request(client, "GET", "https://graph/x")  # type: ignore[arg-type]

        # The last response is handed back so the caller can raise on it.
        assert resp.status_code == 503
        assert waits == [2.0, 4.0, 8.0, 16.0]
        assert len(client.requests) == bds._GRAPH_MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_does_not_retry_a_client_error(self) -> None:
        client = _SequenceClient([_FakeResponse({}, status_code=404)])
        sleep_mock, _ = self._sleep_spy()

        with patch.object(bds.asyncio, "sleep", sleep_mock):
            resp = await bds._graph_request(client, "GET", "https://graph/x")  # type: ignore[arg-type]

        assert resp.status_code == 404
        assert len(client.requests) == 1
        sleep_mock.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unusable_retry_after_falls_back_to_backoff(self) -> None:
        """An HTTP-date Retry-After is not parsed — the backoff takes over."""
        client = _SequenceClient(
            [
                _FakeResponse(
                    {}, status_code=503, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}
                ),
                _FakeResponse({"ok": True}),
            ]
        )
        sleep_mock, waits = self._sleep_spy()

        with patch.object(bds.asyncio, "sleep", sleep_mock):
            await bds._graph_request(client, "GET", "https://graph/x")  # type: ignore[arg-type]

        assert waits == [bds._GRAPH_BACKOFF_BASE]

    @pytest.mark.asyncio
    async def test_retry_after_is_capped(self) -> None:
        client = _SequenceClient(
            [
                _FakeResponse({}, status_code=429, headers={"Retry-After": "3600"}),
                _FakeResponse({"ok": True}),
            ]
        )
        sleep_mock, waits = self._sleep_spy()

        with patch.object(bds.asyncio, "sleep", sleep_mock):
            await bds._graph_request(client, "GET", "https://graph/x")  # type: ignore[arg-type]

        assert waits == [bds._GRAPH_MAX_BACKOFF]


@pytest.mark.asyncio
async def test_children_listing_survives_a_throttled_page() -> None:
    """A 429 in the middle of a paged listing does not lose the folder."""
    page2 = f"{_BASE}/drives/d1/items/folder1/children?$skiptoken=abc"
    calls: list[str] = []
    throttled: set[str] = set()

    class _ThrottleOnceClient:
        async def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
            calls.append(url)
            if url == page2 and url not in throttled:
                throttled.add(url)
                return _FakeResponse({}, status_code=429, headers={"Retry-After": "1"})
            routes: dict[str, dict[str, object]] = {
                f"{_BASE}/drives/d1/root:/backups/pdfs": {"id": "folder1"},
                f"{_BASE}/drives/d1/items/folder1/children{_CHILDREN_Q}": {
                    "value": [{"id": "a", "name": "a.pdf", "size": 1}],
                    "@odata.nextLink": page2,
                },
                page2: {"value": [{"id": "b", "name": "b.pdf", "size": 2}]},
            }
            payload = routes.get(url)
            return _FakeResponse(payload) if payload is not None else _FakeResponse({}, 404)

    with patch.object(bds.asyncio, "sleep", AsyncMock()):
        items = await bds._graph_list_children(_ThrottleOnceClient(), "tok", "d1", "backups/pdfs")  # type: ignore[arg-type]

    assert [i["name"] for i in items] == ["a.pdf", "b.pdf"]
    assert calls.count(page2) == 2  # throttled once, then retried


@pytest.mark.asyncio
async def test_children_listing_tolerates_a_folder_deleted_mid_walk() -> None:
    """A sub-folder removed between the parent listing and its walk yields no files.

    Before, the 404 escalated through raise_for_status() and sank the whole
    mirror — the very failure mode this lot fixes.
    """
    routes = {
        f"{_BASE}/drives/d1/root:/backups/pdfs": {"id": "root1"},
        f"{_BASE}/drives/d1/items/root1/children{_CHILDREN_Q}": {
            "value": [
                {"id": "f1", "name": "facture_A.pdf", "size": 10},
                {"id": "gone", "name": "2025", "folder": {}},
            ]
        },
        # No route for items/gone/children → the fake client answers 404.
    }
    client = _FakeGraphClient(routes)

    files = await bds._graph_list_files(client, "tok", "d1", "backups/pdfs")  # type: ignore[arg-type]

    assert files == {"facture_A.pdf": 10}


@pytest.mark.asyncio
async def test_listing_keeps_pages_collected_before_the_folder_vanished() -> None:
    page2 = f"{_BASE}/drives/d1/items/folder1/children?$skiptoken=abc"
    routes = {
        f"{_BASE}/drives/d1/root:/backups/pdfs": {"id": "folder1"},
        f"{_BASE}/drives/d1/items/folder1/children{_CHILDREN_Q}": {
            "value": [{"id": "a", "name": "a.pdf", "size": 1}],
            "@odata.nextLink": page2,
        },
        # page2 missing → 404 halfway through the listing.
    }
    client = _FakeGraphClient(routes)

    items = await bds._graph_list_children(client, "tok", "d1", "backups/pdfs")  # type: ignore[arg-type]

    assert [i["name"] for i in items] == ["a.pdf"]
