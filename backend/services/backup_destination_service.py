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
            cfg[section] = {
                "type": "onedrive",
                "token": token,
                "drive_id": drive_id,
                "drive_type": extra.get("drive_type", "personal"),
            }
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


async def sync_destination(
    dest: BackupDestination,
    src_paths: list[str],
) -> None:
    """Run ``rclone sync`` for each source path to the destination.

    Raises RuntimeError if rclone returns a non-zero exit code.
    """
    conf = str(_RCLONE_CONF_PATH.resolve())
    for src in src_paths:
        remote = f"{dest.rclone_remote_name}:{dest.target_path}"
        cmd = ["rclone", "sync", src, remote, "--update", "--config", conf]
        logger.debug("rclone sync: %s -> %s", src, remote)
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
