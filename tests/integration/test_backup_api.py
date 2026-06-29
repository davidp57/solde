"""Integration tests for the backup API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.app_settings import AppSettings
from backend.schemas.backup import BackupConnectionTestResult, BackupRestoreTestResult

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True)
async def _init_settings(db_session: AsyncSession) -> None:
    """Ensure AppSettings row (id=1) exists for all backup tests."""
    db_session.add(AppSettings(id=1))
    await db_session.commit()


# ---------------------------------------------------------------------------
# Destinations CRUD
# ---------------------------------------------------------------------------


class TestBackupDestinations:
    async def test_requires_admin(self, client: AsyncClient, secretaire_auth_headers: dict) -> None:
        r = await client.get("/api/backup/destinations", headers=secretaire_auth_headers)
        assert r.status_code == 403

    async def test_list_empty(self, client: AsyncClient, auth_headers: dict) -> None:
        r = await client.get("/api/backup/destinations", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    async def test_create_local(self, client: AsyncClient, auth_headers: dict) -> None:
        payload = {
            "name": "Local NAS",
            "type": "local",
            "rclone_remote_name": "nas-local",
            "target_path": "/mnt/backup",
            "enabled": True,
        }
        with patch(
            "backend.routers.backup._regenerate_rclone_conf",
            new=AsyncMock(),
        ):
            r = await client.post("/api/backup/destinations", json=payload, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Local NAS"
        assert data["type"] == "local"
        assert "id" in data

    async def test_create_then_list(self, client: AsyncClient, auth_headers: dict) -> None:
        payload = {
            "name": "SMB Dest",
            "type": "smb",
            "rclone_remote_name": "nas-smb",
            "target_path": "solde-backup",
            "enabled": False,
        }
        with patch("backend.routers.backup._regenerate_rclone_conf", new=AsyncMock()):
            await client.post("/api/backup/destinations", json=payload, headers=auth_headers)
            r = await client.get("/api/backup/destinations", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

    async def test_update_destination(self, client: AsyncClient, auth_headers: dict) -> None:
        payload = {
            "name": "My Dest",
            "type": "local",
            "rclone_remote_name": "local-bk",
            "target_path": "/backup",
            "enabled": True,
        }
        with patch("backend.routers.backup._regenerate_rclone_conf", new=AsyncMock()):
            create_r = await client.post(
                "/api/backup/destinations", json=payload, headers=auth_headers
            )
            dest_id = create_r.json()["id"]
            update_r = await client.put(
                f"/api/backup/destinations/{dest_id}",
                json={"enabled": False},
                headers=auth_headers,
            )
        assert update_r.status_code == 200
        assert update_r.json()["enabled"] is False

    async def test_delete_destination(self, client: AsyncClient, auth_headers: dict) -> None:
        payload = {
            "name": "To Delete",
            "type": "local",
            "rclone_remote_name": "del-bk",
            "target_path": "/tmp/bk",
            "enabled": True,
        }
        with patch("backend.routers.backup._regenerate_rclone_conf", new=AsyncMock()):
            create_r = await client.post(
                "/api/backup/destinations", json=payload, headers=auth_headers
            )
            dest_id = create_r.json()["id"]
            del_r = await client.delete(f"/api/backup/destinations/{dest_id}", headers=auth_headers)
        assert del_r.status_code == 204

    async def test_test_connection_ok(self, client: AsyncClient, auth_headers: dict) -> None:
        payload = {
            "name": "Test Conn",
            "type": "local",
            "rclone_remote_name": "test-r",
            "target_path": "/tmp",
            "enabled": True,
        }
        ok_result = BackupConnectionTestResult(success=True, message="OK")
        with patch("backend.routers.backup._regenerate_rclone_conf", new=AsyncMock()):
            create_r = await client.post(
                "/api/backup/destinations", json=payload, headers=auth_headers
            )
            dest_id = create_r.json()["id"]
        with patch(
            "backend.services.backup_destination_service.test_destination_connection",
            new=AsyncMock(return_value=ok_result),
        ):
            r = await client.post(
                f"/api/backup/destinations/{dest_id}/test",
                headers=auth_headers,
            )
        assert r.status_code == 200
        assert r.json()["success"] is True


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------


class TestBackupSchedule:
    async def test_get_schedule_defaults(self, client: AsyncClient, auth_headers: dict) -> None:
        r = await client.get("/api/backup/schedule", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "enabled" in data
        assert data["enabled"] is False  # default

    async def test_update_schedule(self, client: AsyncClient, auth_headers: dict) -> None:
        with patch("backend.services.backup_scheduler.reload_scheduler", new=AsyncMock()):
            r = await client.put(
                "/api/backup/schedule",
                json={"enabled": True, "interval_hours": 12},
                headers=auth_headers,
            )
        assert r.status_code == 200
        assert r.json()["enabled"] is True
        assert r.json()["interval_hours"] == 12

    async def test_schedule_requires_admin(
        self, client: AsyncClient, secretaire_auth_headers: dict
    ) -> None:
        r = await client.get("/api/backup/schedule", headers=secretaire_auth_headers)
        assert r.status_code == 403

    async def test_pdfs_only_archived_defaults_false(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        r = await client.get("/api/backup/schedule", headers=auth_headers)
        assert r.json()["pdfs_only_archived"] is False

    async def test_update_pdfs_only_archived(self, client: AsyncClient, auth_headers: dict) -> None:
        with patch("backend.services.backup_scheduler.reload_scheduler", new=AsyncMock()):
            r = await client.put(
                "/api/backup/schedule",
                json={"pdfs_only_archived": True},
                headers=auth_headers,
            )
        assert r.status_code == 200
        assert r.json()["pdfs_only_archived"] is True
        g = await client.get("/api/backup/schedule", headers=auth_headers)
        assert g.json()["pdfs_only_archived"] is True


# ---------------------------------------------------------------------------
# Run now + Status
# ---------------------------------------------------------------------------


class TestBackupRunAndStatus:
    async def test_run_now(self, client: AsyncClient, auth_headers: dict) -> None:
        with patch("backend.services.backup_scheduler.run_backup_job", new=AsyncMock()):
            r = await client.post("/api/backup/run", headers=auth_headers)
        assert r.status_code == 202

    async def test_get_status(self, client: AsyncClient, auth_headers: dict) -> None:
        r = await client.get("/api/backup/status", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "last_run_at" in data


# ---------------------------------------------------------------------------
# Test-restore
# ---------------------------------------------------------------------------


class TestBackupTestRestore:
    async def test_invalid_filename_rejected(self, client: AsyncClient, auth_headers: dict) -> None:
        r = await client.post(
            "/api/backup/backups/INVALID_FILENAME.db/test-restore",
            headers=auth_headers,
        )
        assert r.status_code == 400

    async def test_valid_filename_calls_service(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        ok_result = BackupRestoreTestResult(
            ok=True,
            integrity_check="ok",
            tables_found=set(),
            tables_missing=[],
        )
        with patch(
            "backend.services.backup_restore_service.test_restore",
            new=AsyncMock(return_value=ok_result),
        ):
            r = await client.post(
                "/api/backup/backups/solde_backup_20260510_120000.db/test-restore",
                headers=auth_headers,
            )
        assert r.status_code == 200
        assert r.json()["ok"] is True
