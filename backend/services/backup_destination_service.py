"""Service for rclone-based backup destinations.

Provides:
- write_rclone_config: regenerates data/rclone.conf from DB destinations
- sync_destination: syncs local paths to a remote destination
- test_destination_connection: verifies connectivity to a destination
- fetch_remote_backup: copies a remote backup file locally before restore

OneDrive destinations bypass rclone and upload directly via Microsoft Graph API
because rclone v1.60 DEV has a broken upload-session implementation for personal
OneDrive accounts.  Graph API uploads are made with httpx.
"""

import asyncio
import configparser
import io
import json
import logging
import re
import urllib.parse
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

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
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    """Sync local paths to a remote destination under a dated sub-folder.

    Files land under ``<target_path>/<run_ts>/<source_name>/``.
    OneDrive destinations use the Microsoft Graph API directly (bypassing
    rclone's broken upload-session in v1.60 DEV).  All other destination
    types use ``rclone copy``.

    ``on_progress(done, total)`` is called after each uploaded file (OneDrive)
    or at start/end (rclone, no per-file info available).

    Raises RuntimeError on failure.
    """
    if dest.type == "onedrive" and on_progress is not None:
        # Pre-count all files across every source path to report unified progress.
        total_files = sum(
            (1 if Path(s).is_file() else sum(1 for p in Path(s).rglob("*") if p.is_file()))
            for s in src_paths
        )
        counter: list[int] = [0]

        def _on_file() -> None:
            counter[0] += 1
            on_progress(counter[0], total_files)

        _file_cb: Callable[[], None] | None = _on_file
    else:
        _file_cb = None

    for i, src in enumerate(src_paths):
        src_path = Path(src)
        # Single-file: place under <run_ts>/<parent_dir_name>/; directory: use its own name
        subdir = src_path.parent.name if src_path.is_file() else src_path.name
        base = dest.target_path.rstrip("/") if dest.target_path else ""
        remote_path = f"{base}/{run_ts}/{subdir}" if base else f"{run_ts}/{subdir}"

        if dest.type == "onedrive":
            if src_path.is_file():
                # Upload a single file directly (no directory traversal needed)
                async with httpx.AsyncClient() as client:
                    config = json.loads(dest.rclone_config or "{}")
                    drive_id = config.get("drive_id", "")
                    access_token = _graph_access_token(dest)
                    file_remote = f"{remote_path}/{src_path.name}"
                    logger.info(
                        "Graph upload: %s → drives/%s/root:/%s",
                        src_path.name,
                        drive_id,
                        file_remote,
                    )
                    await _graph_upload_file(client, access_token, drive_id, file_remote, src_path)
                    if _file_cb is not None:
                        _file_cb()
            else:
                await _graph_upload_dir(dest, src_path, remote_path, on_file_uploaded=_file_cb)
        else:
            if on_progress is not None:
                on_progress(i, len(src_paths))
            conf = str(_RCLONE_CONF_PATH.resolve())
            remote = f"{dest.rclone_remote_name}:{remote_path}"
            cmd = ["rclone", "copy", src, remote, "--config", conf]
            logger.info("rclone copy: %s -> %s", src, remote)
            await _run_rclone(cmd)
            if on_progress is not None:
                on_progress(i + 1, len(src_paths))


# ---------------------------------------------------------------------------
# Microsoft Graph API upload helpers (OneDrive)
# ---------------------------------------------------------------------------

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_GRAPH_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MiB — must be a multiple of 320 KiB
_GRAPH_SMALL_LIMIT = 4 * 1024 * 1024  # use simple PUT below 4 MiB


def _graph_access_token(dest: BackupDestination) -> str:
    """Extract the current access_token from dest.rclone_config."""
    if not dest.rclone_config:
        raise RuntimeError(f"OneDrive dest {dest.id} has no rclone_config")
    config = json.loads(dest.rclone_config)
    token = json.loads(config.get("token", "{}"))
    access_token = token.get("access_token", "")
    if not access_token:
        raise RuntimeError(f"OneDrive dest {dest.id}: no access_token in config")
    return str(access_token)


async def _graph_upload_file(
    client: httpx.AsyncClient,
    access_token: str,
    drive_id: str,
    remote_path: str,
    local_file: Path,
) -> None:
    """Upload one file to OneDrive via Microsoft Graph API.

    Uses a simple PUT for files ≤ 4 MiB and an upload session for larger files.
    ``remote_path`` is a OneDrive path relative to the drive root, e.g.
    ``solde/backups/2026-05-11T14-00-00/backups/solde_backup_20260511.db``.
    """
    file_size = local_file.stat().st_size
    auth = {"Authorization": f"Bearer {access_token}"}
    encoded = urllib.parse.quote(remote_path)

    # Drive-relative endpoint works for both personal and business drives.
    item_url = f"{_GRAPH_BASE}/drives/{drive_id}/root:/{encoded}"

    if file_size <= _GRAPH_SMALL_LIMIT:
        # Simple PUT
        content = local_file.read_bytes()
        resp = await client.put(
            f"{item_url}:/content",
            headers={**auth, "Content-Type": "application/octet-stream"},
            content=content,
            timeout=60,
        )
        resp.raise_for_status()
        logger.debug("Graph PUT %s → %d", local_file.name, resp.status_code)
    else:
        # Create upload session
        resp = await client.post(
            f"{item_url}:/createUploadSession",
            headers=auth,
            json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
            timeout=30,
        )
        resp.raise_for_status()
        upload_url: str = resp.json()["uploadUrl"]

        # Upload chunks — personal OneDrive upload session URLs are pre-authenticated
        # (SAS-style). Do NOT include the Authorization header for segment PUTs.
        uploaded = 0
        with local_file.open("rb") as fh:
            while uploaded < file_size:
                chunk = fh.read(_GRAPH_CHUNK_SIZE)
                if not chunk:
                    break
                end = uploaded + len(chunk) - 1
                chunk_resp = await client.put(
                    upload_url,
                    headers={
                        "Content-Range": f"bytes {uploaded}-{end}/{file_size}",
                        "Content-Type": "application/octet-stream",
                    },
                    content=chunk,
                    timeout=120,
                )
                if chunk_resp.status_code not in (200, 201, 202):
                    chunk_resp.raise_for_status()
                uploaded += len(chunk)
                logger.debug(
                    "Graph chunk %s: %d/%d bytes uploaded",
                    local_file.name,
                    uploaded,
                    file_size,
                )
        logger.info("Graph upload session %s → done (%d bytes)", local_file.name, file_size)


async def _graph_upload_dir(
    dest: BackupDestination,
    src_dir: Path,
    remote_path: str,
    on_file_uploaded: Callable[[], None] | None = None,
) -> None:
    """Upload all files from ``src_dir`` to ``remote_path`` on OneDrive.

    Recurses into sub-directories, preserving the relative path structure.
    Calls ``on_file_uploaded()`` after each successful file upload.
    """
    if not dest.rclone_config:
        raise RuntimeError(f"OneDrive dest {dest.id} has no rclone_config")
    config = json.loads(dest.rclone_config)
    drive_id = config.get("drive_id", "")
    access_token = _graph_access_token(dest)

    if not src_dir.is_dir():
        logger.info("Graph upload: %s is not a directory, skipping", src_dir)
        return

    all_files = sorted(p for p in src_dir.rglob("*") if p.is_file())
    if not all_files:
        logger.info("Graph upload: no files under %s, skipping", src_dir)
        return

    async with httpx.AsyncClient() as client:
        for local_file in all_files:
            rel = local_file.relative_to(src_dir)
            file_remote = f"{remote_path}/{rel.as_posix()}"
            logger.info(
                "Graph upload: %s → drives/%s/root:/%s",
                rel,
                drive_id,
                file_remote,
            )
            await _graph_upload_file(client, access_token, drive_id, file_remote, local_file)
            if on_file_uploaded is not None:
                on_file_uploaded()


async def test_destination_connection(dest: BackupDestination) -> BackupConnectionTestResult:
    """Run ``rclone lsd`` to verify the destination is reachable."""
    conf = str(_RCLONE_CONF_PATH.resolve())
    remote = f"{dest.rclone_remote_name}:"
    cmd = ["rclone", "lsd", remote, "--config", conf]
    try:
        await _run_rclone(cmd)
        return BackupConnectionTestResult(success=True, message="Connexion réussie")
    except RuntimeError as exc:
        logger.warning("Destination connection test failed for dest %s: %s", dest.id, exc)
        return BackupConnectionTestResult(
            success=False,
            message="Connexion impossible. Vérifiez les paramètres de la destination.",
        )


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


# ---------------------------------------------------------------------------
# Remote retention — prune old timestamped snapshot folders (TEC-208)
# ---------------------------------------------------------------------------

# Matches a backup snapshot folder name, e.g. "2026-06-13T02-00-04".
_BACKUP_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$")


async def _graph_list_children(
    client: httpx.AsyncClient, access_token: str, drive_id: str, base: str
) -> list[dict[str, object]]:
    """List the immediate children (files + folders) of a OneDrive folder.

    ``base`` is the drive-relative path of the parent folder (empty = drive root).
    Returns the raw Graph item dicts (each has ``id``, ``name`` and, for folders,
    a ``folder`` facet). Returns ``[]`` if the folder does not exist yet.
    """
    auth = {"Authorization": f"Bearer {access_token}"}
    if base:
        encoded = urllib.parse.quote(base)
        url: str | None = f"{_GRAPH_BASE}/drives/{drive_id}/root:/{encoded}:/children"
    else:
        url = f"{_GRAPH_BASE}/drives/{drive_id}/root/children"
    items: list[dict[str, object]] = []
    while url:
        resp = await client.get(url, headers=auth, timeout=30)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return items


async def _graph_delete_item(
    client: httpx.AsyncClient, access_token: str, drive_id: str, item_id: str
) -> None:
    """Delete a OneDrive item (folder or file) by its id."""
    auth = {"Authorization": f"Bearer {access_token}"}
    resp = await client.delete(
        f"{_GRAPH_BASE}/drives/{drive_id}/items/{item_id}", headers=auth, timeout=30
    )
    if resp.status_code not in (200, 204, 404):
        resp.raise_for_status()


async def prune_remote_backups(dest: BackupDestination, keep: int = 5) -> int:
    """Delete timestamped backup **snapshot** folders beyond the ``keep`` most recent.

    Targets only folders whose name matches the run-timestamp pattern
    (``YYYY-MM-DDTHH-MM-SS``) directly under the destination's ``target_path``.
    Stable mirror folders (e.g. ``pdfs/``, ``uploads/``, introduced by TEC-209)
    never match the pattern and are therefore never pruned.

    Returns the number of snapshot folders deleted. Raises on a hard failure;
    the caller treats pruning as best-effort.
    """
    if keep < 1:
        raise ValueError("keep must be >= 1")
    base = (dest.target_path or "").rstrip("/")

    if dest.type == "onedrive":
        config = json.loads(dest.rclone_config or "{}")
        drive_id = config.get("drive_id", "")
        access_token = _graph_access_token(dest)
        async with httpx.AsyncClient() as client:
            children = await _graph_list_children(client, access_token, drive_id, base)
            snapshots = sorted(
                (
                    (str(c.get("name", "")), str(c.get("id", "")))
                    for c in children
                    if c.get("folder") is not None and _BACKUP_TS_RE.match(str(c.get("name", "")))
                ),
                key=lambda nm: nm[0],
            )
            to_delete = snapshots[:-keep] if len(snapshots) > keep else []
            for name, item_id in to_delete:
                await _graph_delete_item(client, access_token, drive_id, item_id)
                logger.info("Pruned remote snapshot %s (dest %s)", name, dest.id)
            return len(to_delete)

    # rclone-based destinations (SMB, local, …)
    conf = str(_RCLONE_CONF_PATH.resolve())
    remote_base = f"{dest.rclone_remote_name}:{base}" if base else f"{dest.rclone_remote_name}:"
    out = await _run_rclone(["rclone", "lsf", "--dirs-only", remote_base, "--config", conf])
    names = sorted(
        n.rstrip("/") for n in out.splitlines() if _BACKUP_TS_RE.match(n.strip().rstrip("/"))
    )
    to_delete_names = names[:-keep] if len(names) > keep else []
    for name in to_delete_names:
        await _run_rclone(["rclone", "purge", f"{remote_base}/{name}", "--config", conf])
        logger.info("Pruned remote snapshot %s (dest %s)", name, dest.id)
    return len(to_delete_names)


# ---------------------------------------------------------------------------
# Incremental mirror — stable folders for immutable assets (TEC-209)
# ---------------------------------------------------------------------------


async def _graph_list_files(
    client: httpx.AsyncClient, access_token: str, drive_id: str, base: str
) -> dict[str, int]:
    """Recursively map ``relpath -> size`` for every file under ``base``.

    Used to diff a OneDrive mirror folder against the local directory so only
    missing/changed files are uploaded. Empty dict if the folder is absent.
    """
    files: dict[str, int] = {}

    async def _walk(folder_path: str, rel_prefix: str) -> None:
        for child in await _graph_list_children(client, access_token, drive_id, folder_path):
            name = str(child.get("name", ""))
            rel = f"{rel_prefix}{name}"
            if child.get("folder") is not None:
                await _walk(f"{folder_path}/{name}", f"{rel}/")
            else:
                size = child.get("size", 0)
                files[rel] = size if isinstance(size, int) else 0

    await _walk(base, "")
    return files


async def archived_pdf_relpaths(db: AsyncSession) -> set[str]:
    """Filenames (relative to ``data/pdfs``) of non-regenerable invoice PDFs.

    Only archived invoices carry legal-value, non-regenerable PDFs (BIZ-216);
    every other PDF is rebuilt on demand (TEC-211), so it need not be mirrored.
    """
    from sqlalchemy import select  # noqa: PLC0415

    from backend.models.invoice import Invoice, InvoiceStatus  # noqa: PLC0415

    result = await db.execute(
        select(Invoice.pdf_path).where(
            Invoice.status == InvoiceStatus.ARCHIVED,
            Invoice.pdf_path.is_not(None),
        )
    )
    return {Path(p).name for p in result.scalars().all() if p}


async def mirror_dir_incremental(
    dest: BackupDestination,
    local_dir: str,
    remote_subdir: str,
    allowed_relpaths: set[str] | None = None,
) -> int:
    """Mirror ``local_dir`` to a **stable** remote folder, uploading only new files.

    Unlike the timestamped snapshot, the mirror lives at a fixed remote path
    (``<target_path>/<remote_subdir>``) and is **append-only** (never pruned),
    so immutable assets (PDFs, uploads) are stored once instead of being
    re-uploaded on every backup. Returns the number of files uploaded
    (0 for rclone, which performs its own incremental copy).

    When *allowed_relpaths* is given, only files whose path relative to
    *local_dir* is in the set are mirrored (BIZ-216 PDF filtering); ``None``
    (default) mirrors everything.
    """
    local = Path(local_dir)
    if not local.is_dir():
        return 0
    base = (dest.target_path or "").rstrip("/")
    remote_base = f"{base}/{remote_subdir}".strip("/")

    if dest.type == "onedrive":
        config = json.loads(dest.rclone_config or "{}")
        drive_id = config.get("drive_id", "")
        access_token = _graph_access_token(dest)
        uploaded = 0
        async with httpx.AsyncClient() as client:
            remote_files = await _graph_list_files(client, access_token, drive_id, remote_base)
            for local_file in sorted(p for p in local.rglob("*") if p.is_file()):
                rel = local_file.relative_to(local).as_posix()
                if allowed_relpaths is not None and rel not in allowed_relpaths:
                    continue  # filtered out (BIZ-216)
                if remote_files.get(rel) == local_file.stat().st_size:
                    continue  # already present with the same size — skip
                await _graph_upload_file(
                    client, access_token, drive_id, f"{remote_base}/{rel}", local_file
                )
                uploaded += 1
        if uploaded:
            logger.info("Mirrored %d file(s) to %s (dest %s)", uploaded, remote_subdir, dest.id)
        return uploaded

    # rclone destinations: `rclone copy` to a stable folder is already incremental
    # (skips files identical by size/modtime).
    conf = str(_RCLONE_CONF_PATH.resolve())
    remote = f"{dest.rclone_remote_name}:{remote_base}"
    if allowed_relpaths is not None:
        # Restrict the copy to the allowed files via a temporary --files-from list.
        import tempfile  # noqa: PLC0415

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
            fh.write("\n".join(sorted(allowed_relpaths)))
            files_from = fh.name
        try:
            await _run_rclone(
                [
                    "rclone",
                    "copy",
                    str(local.resolve()),
                    remote,
                    "--files-from",
                    files_from,
                    "--config",
                    conf,
                ]
            )
        finally:
            Path(files_from).unlink(missing_ok=True)
        return 0

    await _run_rclone(["rclone", "copy", str(local.resolve()), remote, "--config", conf])
    return 0


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
        logger.error("rclone command failed (code %d): %s", proc.returncode, err)
        raise RuntimeError(f"rclone: {_rclone_summary(err)}")

    return stdout.decode(errors="replace")
