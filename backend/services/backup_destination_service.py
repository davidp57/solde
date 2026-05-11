"""Service for rclone-based backup destinations.

Provides:
- write_rclone_config: regenerates data/rclone.conf from DB destinations
- sync_destination: runs ``rclone sync`` for a given destination
- test_destination_connection: runs ``rclone lsd`` to verify connectivity
- fetch_remote_backup: copies a remote backup file locally before restore
"""

import asyncio
import configparser
import io
import json
import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from backend.models.backup_destination import BackupDestination
from backend.schemas.backup import BackupConnectionTestResult

logger = logging.getLogger(__name__)

_RCLONE_CONF_PATH = Path("data/rclone.conf")


def _build_rclone_conf(destinations: list[BackupDestination]) -> str:
    """Generate rclone.conf content from a list of BackupDestination rows."""
    cfg = configparser.ConfigParser()
    for dest in destinations:
        section = dest.rclone_remote_name
        extra: dict[str, str] = {}
        if dest.rclone_config:
            try:
                extra = json.loads(dest.rclone_config)
            except (json.JSONDecodeError, ValueError):
                logger.warning("Invalid JSON rclone_config for destination %s", dest.id)

        if dest.type == "local":
            cfg[section] = {"type": "local"}
        elif dest.type == "smb":
            cfg[section] = {
                "type": "smb",
                "host": extra.get("host", ""),
                "user": extra.get("user", ""),
                "pass": extra.get("pass", ""),
                "domain": extra.get("domain", ""),
            }
        elif dest.type == "onedrive":
            token = extra.get("token", "{}")
            drive_id = extra.get("drive_id", "")
            section_cfg: dict[str, str] = {
                "type": "onedrive",
                "token": token,
                "drive_id": drive_id,
                "drive_type": extra.get("drive_type", "personal"),
            }
            # Include the client_id used to obtain the token so that rclone uses
            # the same app when refreshing — mandatory for non-rclone client IDs.
            if extra.get("client_id"):
                section_cfg["client_id"] = extra["client_id"]
                section_cfg["client_secret"] = extra.get("client_secret", "")
            cfg[section] = section_cfg
        else:
            cfg[section] = {"type": dest.type}
            cfg[section].update(extra)

    buf = io.StringIO()
    cfg.write(buf)
    return buf.getvalue()


def write_rclone_config(destinations: list[BackupDestination]) -> None:
    """Write (or overwrite) data/rclone.conf from DB destinations."""
    _RCLONE_CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = _build_rclone_conf(destinations)
    _RCLONE_CONF_PATH.write_text(content, encoding="utf-8")
    logger.debug("rclone.conf written (%d destinations)", len(destinations))


async def refresh_onedrive_tokens(destinations: list[BackupDestination]) -> None:
    """Pre-refresh expired OneDrive OAuth tokens in-place before backup.

    Updates ``dest.rclone_config`` in memory so the caller can immediately
    call ``write_rclone_config``.  Also persists the new token to the DB
    so future runs start with a fresh token.
    """
    import httpx

    for dest in destinations:
        if dest.type != "onedrive" or not dest.rclone_config:
            continue
        try:
            config = json.loads(dest.rclone_config)
            token = json.loads(config.get("token", "{}"))
            expiry_str = token.get("expiry", "")
            if not expiry_str:
                continue

            # Normalize nanoseconds and parse expiry
            expiry = datetime.fromisoformat(expiry_str[:19] + "+00:00")
            if expiry > datetime.now(UTC) + timedelta(minutes=5):
                continue  # Token still valid for at least 5 minutes

            refresh_token = token.get("refresh_token", "")
            client_id = config.get("client_id", "")
            if not refresh_token or not client_id:
                logger.warning(
                    "OneDrive dest %s: expired token but missing refresh_token/client_id",
                    dest.id,
                )
                continue

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": client_id,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                )

            if not resp.is_success:
                logger.warning(
                    "OneDrive token refresh failed for dest %s: %s",
                    dest.id,
                    resp.text[:300],
                )
                continue

            data = resp.json()
            if "access_token" not in data:
                logger.warning("No access_token in refresh response for dest %s", dest.id)
                continue

            new_expiry = datetime.now(UTC) + timedelta(seconds=int(data.get("expires_in", 3600)))
            new_token = {
                "access_token": data["access_token"],
                "token_type": data.get("token_type", "Bearer"),
                "refresh_token": data.get("refresh_token", refresh_token),
                "expiry": new_expiry.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
            }
            config["token"] = json.dumps(new_token)
            dest.rclone_config = json.dumps(config)
            logger.info(
                "Pre-refreshed OneDrive token for dest %s (new expiry: %s)",
                dest.id,
                new_expiry.isoformat(),
            )

        except Exception as exc:
            logger.warning("OneDrive token pre-refresh error for dest %s: %s", dest.id, exc)


async def sync_destination(
    dest: BackupDestination,
    src_paths: list[str],
    run_ts: str,
) -> None:
    """Run ``rclone copy`` for each source path to the destination.

    Files are placed under a dated sub-folder named after the backup run
    timestamp (``run_ts``, format ``YYYY-MM-DDTHH-MM-SS``) so every backup
    run creates its own directory at the destination.

    Example: target_path=solde, run_ts=2026-05-11T14-30-00
      → solde/2026-05-11T14-30-00/backups/
      → solde/2026-05-11T14-30-00/uploads/

    Raises RuntimeError if rclone returns a non-zero exit code.
    """
    conf = str(_RCLONE_CONF_PATH.resolve())
    for src in src_paths:
        subdir = Path(src).name  # "backups", "uploads", etc.
        base = dest.target_path.rstrip("/") if dest.target_path else ""
        remote_path = f"{base}/{run_ts}/{subdir}" if base else f"{run_ts}/{subdir}"
        remote = f"{dest.rclone_remote_name}:{remote_path}"
        cmd = ["rclone", "copy", src, remote, "--config", conf]
        logger.info("rclone copy: %s -> %s", src, remote)
        await _run_rclone(cmd)


async def test_destination_connection(dest: BackupDestination) -> BackupConnectionTestResult:
    """Run ``rclone lsd`` to verify the destination is reachable."""
    conf = str(_RCLONE_CONF_PATH.resolve())
    remote = f"{dest.rclone_remote_name}:"
    cmd = ["rclone", "lsd", remote, "--config", conf]
    try:
        await _run_rclone(cmd)
        return BackupConnectionTestResult(success=True, message="Connexion réussie")
    except RuntimeError as exc:
        return BackupConnectionTestResult(success=False, message=str(exc))


async def fetch_remote_backup(
    dest: BackupDestination,
    filename: str,
    backup_dir: str,
) -> None:
    """Copy a backup file from a remote destination to the local backup dir."""
    conf = str(_RCLONE_CONF_PATH.resolve())
    remote = f"{dest.rclone_remote_name}:{dest.target_path}"
    local_dir = str(Path(backup_dir).resolve())
    cmd = ["rclone", "copy", f"{remote}/{filename}", local_dir, "--config", conf]
    logger.info("Fetching remote backup %s from %s", filename, remote)
    await _run_rclone(cmd)


_RCLONE_TS_RE = re.compile(r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} (?:ERROR : |WARNING: )?")


def _rclone_summary(stderr: str) -> str:
    """Return the last meaningful rclone stderr line, with timestamp stripped."""
    lines = [ln.strip() for ln in stderr.splitlines() if ln.strip()]
    if not lines:
        return "Erreur rclone inconnue"
    return _RCLONE_TS_RE.sub("", lines[-1]) or "Erreur rclone inconnue"


async def _run_rclone(cmd: list[str]) -> str:
    """Execute an rclone command asynchronously; raises RuntimeError on failure."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
    except FileNotFoundError as exc:
        raise RuntimeError("rclone n'est pas installé ou introuvable dans le PATH") from exc

    if proc.returncode != 0:
        err = stderr.decode(errors="replace").strip()
        raise RuntimeError(f"rclone (code {proc.returncode}): {_rclone_summary(err)}")

    return stdout.decode(errors="replace")
