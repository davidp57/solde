"""Backup scheduler — APScheduler wrapper for automated database backups.

Manages a single recurring job that:
1. Creates a local SQLite backup.
2. Syncs to every enabled destination via rclone.
3. Updates backup_last_run_at / backup_last_run_status in app_settings.
4. Sends a failure notification email when configured.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from backend.models.app_settings import AppSettings
from backend.models.backup_destination import BackupDestination

logger = logging.getLogger(__name__)

_JOB_ID = "backup_job"

# Remote retention: number of most-recent timestamped snapshots kept per
# destination (aligned with the local rotation in backup_service).
_REMOTE_BACKUP_RETENTION = 5

# Module-level scheduler instance shared across requests
_scheduler: AsyncIOScheduler | None = None

# In-memory flag — True while run_backup_job is executing
_backup_running: bool = False

# In-memory progress 0–100 — updated at each step of the active backup
_backup_progress: int = 0


def is_backup_running() -> bool:
    """Return True if a backup job is currently executing."""
    return _backup_running


def get_backup_progress() -> int:
    """Return the current backup progress percentage (0–100)."""
    return _backup_progress


def _set_progress(pct: int) -> None:
    global _backup_progress
    _backup_progress = max(0, min(100, pct))


def get_scheduler() -> AsyncIOScheduler:
    """Return the module-level scheduler (lazy init)."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def start_scheduler() -> None:
    """Start the scheduler (idempotent)."""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("Backup scheduler started")


def stop_scheduler() -> None:
    """Shutdown the scheduler gracefully."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Backup scheduler stopped")
    _scheduler = None


def reload_scheduler(settings: AppSettings) -> None:
    """Replan the backup job based on the current settings.

    Called from the router whenever backup schedule settings are updated.
    """
    sched = get_scheduler()
    if not sched.running:
        sched.start()

    # Remove existing job if present
    if sched.get_job(_JOB_ID):
        sched.remove_job(_JOB_ID)

    if not settings.backup_enabled:
        logger.info("Backup is disabled — no job scheduled")
        return

    db_path = _resolve_db_path()
    backup_dir = str(Path("data/backups").resolve())
    include_uploads = settings.backup_include_uploads
    include_all_backups = settings.backup_include_all_backups
    notify_on_failure = settings.backup_notify_on_failure

    trigger: IntervalTrigger | CronTrigger
    if settings.backup_schedule_type == "daily":
        raw_time = (settings.backup_daily_time or "02:00").strip()
        parts = raw_time.split(":")
        hour = int(parts[0]) if len(parts) >= 1 else 2
        minute = int(parts[1]) if len(parts) >= 2 else 0
        trigger = CronTrigger(hour=hour, minute=minute)
        logger.info("Backup scheduled daily at %02d:%02d", hour, minute)
    elif settings.backup_schedule_type == "cron" and settings.backup_cron_expression:
        trigger = CronTrigger.from_crontab(settings.backup_cron_expression)
        logger.info("Backup scheduled via cron: %s", settings.backup_cron_expression)
    else:
        hours = max(1, settings.backup_interval_hours)
        trigger = IntervalTrigger(hours=hours)
        logger.info("Backup scheduled every %d hour(s)", hours)

    sched.add_job(
        run_backup_job,
        trigger=trigger,
        id=_JOB_ID,
        kwargs={
            "db_path": db_path,
            "backup_dir": backup_dir,
            "include_uploads": include_uploads,
            "include_all_backups": include_all_backups,
            "notify_on_failure": notify_on_failure,
        },
        replace_existing=True,
        misfire_grace_time=3600,
    )


def _resolve_db_path() -> str:
    """Derive the SQLite db file path from the configured database_url."""
    from backend.config import get_settings

    url = get_settings().database_url
    # Strip SQLAlchemy driver prefix: sqlite+aiosqlite:///data/solde.db
    if ":///" in url:
        return url.split("///", 1)[1]
    return "data/solde.db"


async def run_backup_job(
    db_path: str,
    backup_dir: str,
    include_uploads: bool,
    notify_on_failure: bool,
    include_all_backups: bool = False,
) -> None:
    """Execute one backup cycle (called by the scheduler)."""
    global _backup_running
    _backup_running = True
    _set_progress(0)
    try:
        await _run_backup_job_inner(
            db_path=db_path,
            backup_dir=backup_dir,
            include_uploads=include_uploads,
            include_all_backups=include_all_backups,
            notify_on_failure=notify_on_failure,
        )
    finally:
        _backup_running = False


async def _run_backup_job_inner(
    db_path: str,
    backup_dir: str,
    include_uploads: bool,
    notify_on_failure: bool,
    include_all_backups: bool = False,
) -> None:
    """Execute one backup cycle (called by the scheduler)."""
    from backend.database import get_session
    from backend.services.backup_destination_service import (
        mirror_dir_incremental,
        prune_remote_backups,
        refresh_onedrive_tokens,
        sync_destination,
        write_rclone_config,
    )
    from backend.services.backup_service import create_backup

    logger.info("Starting scheduled backup")
    overall_success = True
    error_details: list[str] = []

    # Step 1 — create local backup
    _set_progress(0)
    try:
        backup_file = await create_backup(db_path=db_path, backup_dir=backup_dir)
        logger.info("Backup created: %s", backup_file)
        _set_progress(5)
    except Exception as exc:
        logger.error("Backup creation failed: %s", exc, exc_info=exc)
        await _update_run_status(False, f"Backup creation failed: {exc}")
        if notify_on_failure:
            await _send_failure_email(str(exc))
        return

    # Step 1b — validate the new backup (integrity check)
    try:
        from backend.services.backup_restore_service import test_restore

        validation = await test_restore(str(backup_file))
        if not validation.ok:
            detail = validation.error or (
                f"integrity={validation.integrity_check}, missing={validation.tables_missing}"
            )
            logger.error("Backup validation failed for %s: %s", backup_file.name, detail)
            await _update_run_status(False, f"Validation échouée : {detail}")
            if notify_on_failure:
                await _send_failure_email(f"Validation du backup échouée : {detail}")
            return
        logger.info("Backup validated OK: %s", backup_file.name)
    except Exception as exc:
        logger.warning("Backup validation error (non-blocking): %s", exc)
    _set_progress(10)

    # Step 2 — sync to destinations
    async with get_session() as db:
        result = await db.execute(
            select(BackupDestination).where(BackupDestination.enabled.is_(True))
        )
        destinations = list(result.scalars().all())
        # Pre-refresh expired OneDrive tokens so rclone always starts with a
        # valid access_token (avoids relying on rclone's own refresh mechanism).
        await refresh_onedrive_tokens(destinations)
        if any(d.type == "onedrive" for d in destinations):
            # Persist refreshed tokens back to DB in the same session.
            await db.commit()

    if destinations:
        write_rclone_config(destinations)
        run_ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        # The timestamped snapshot carries only the database now. Immutable
        # assets (PDFs, uploads) are mirrored incrementally to stable folders
        # below (TEC-209) instead of being re-bundled on every run.
        # When include_all_backups is True, send the entire backups directory.
        if include_all_backups:
            src_paths: list[str] = [backup_dir]
        else:
            src_paths = [str(backup_file)]

        dest_count = len(destinations)
        for i, dest in enumerate(destinations):
            # Allocate a slice of 10–100% per destination
            dest_start = 10 + int(90 * i / dest_count)
            dest_end = 10 + int(90 * (i + 1) / dest_count)
            _set_progress(dest_start)

            def _make_progress_cb(start: int, end: int) -> Callable[[int, int], None]:
                def cb(done: int, total: int) -> None:
                    if total > 0:
                        _set_progress(start + int((end - start) * done / total))

                return cb

            try:
                await sync_destination(
                    dest, src_paths, run_ts, on_progress=_make_progress_cb(dest_start, dest_end)
                )
                logger.info("Synced to destination %s (%s)", dest.name, dest.type)
                # Incremental mirror of immutable assets to stable folders (TEC-209):
                # uploaded once, never duplicated across snapshots.
                pdfs_dir = Path("data/pdfs")
                if pdfs_dir.exists():
                    await mirror_dir_incremental(dest, str(pdfs_dir.resolve()), "pdfs")
                if include_uploads:
                    uploads_dir = Path("data/uploads")
                    if uploads_dir.exists():
                        await mirror_dir_incremental(dest, str(uploads_dir.resolve()), "uploads")
                # Remote retention: prune old timestamped snapshots (keep N most
                # recent). Best-effort — never fail the backup over pruning.
                try:
                    pruned = await prune_remote_backups(dest, keep=_REMOTE_BACKUP_RETENTION)
                    if pruned:
                        logger.info("Pruned %d old snapshot(s) on %s", pruned, dest.name)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Remote prune failed for %s: %s", dest.name, exc)
            except Exception as exc:
                overall_success = False
                msg = f"{dest.name}: {exc}"
                error_details.append(msg)
                logger.error("Sync failed for destination %s: %s", dest.name, exc)
            finally:
                _set_progress(dest_end)

    # Step 3 — update status
    status_str = "success" if overall_success else "failure"
    await _update_run_status(overall_success, "; ".join(error_details) if error_details else None)

    if not overall_success and notify_on_failure:
        await _send_failure_email("; ".join(error_details))

    logger.info("Backup job finished: %s", status_str)


async def _update_run_status(success: bool, error: str | None) -> None:
    """Persist last_run_at, last_run_status and last_run_error to app_settings."""
    from backend.database import get_session

    async with get_session() as db:
        result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
        settings = result.scalar_one_or_none()
        if settings:
            settings.backup_last_run_at = datetime.now()
            settings.backup_last_run_status = "success" if success else "failure"
            settings.backup_last_run_error = error[:1000] if error else None
            await db.commit()


async def _send_failure_email(error: str) -> None:
    """Send a notification email on backup failure if SMTP is configured."""
    try:
        from backend.database import get_session
        from backend.models.app_settings import AppSettings
        from backend.services.email_service import send_plain_email

        async with get_session() as db:
            result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
            settings = result.scalar_one_or_none()

        if settings and settings.smtp_host and settings.smtp_from_email:
            recipient = settings.smtp_from_email
            send_plain_email(
                host=settings.smtp_host,
                port=settings.smtp_port,
                user=settings.smtp_user,
                password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
                from_email=settings.smtp_from_email,
                to_email=recipient,
                subject="[Solde] Échec de la sauvegarde automatique",
                body=f"La sauvegarde automatique a échoué.\n\nDétails :\n{error}",
            )
    except Exception as exc:
        logger.warning("Could not send backup failure notification: %s", exc)
