"""Backup scheduler — APScheduler wrapper for automated database backups.

Manages a single recurring job that:
1. Creates a local SQLite backup.
2. Syncs to every enabled destination via rclone.
3. Updates backup_last_run_at / backup_last_run_status in app_settings.
4. Sends a failure notification email when configured.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from backend.models.app_settings import AppSettings
from backend.models.backup_destination import BackupDestination

logger = logging.getLogger(__name__)

_JOB_ID = "backup_job"

# Module-level scheduler instance shared across requests
_scheduler: AsyncIOScheduler | None = None


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
    notify_on_failure = settings.backup_notify_on_failure

    trigger: IntervalTrigger | CronTrigger
    if settings.backup_schedule_type == "cron" and settings.backup_cron_expression:
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
) -> None:
    """Execute one backup cycle (called by the scheduler)."""
    from backend.database import get_session
    from backend.services.backup_destination_service import (
        sync_destination,
        write_rclone_config,
    )
    from backend.services.backup_service import create_backup

    logger.info("Starting scheduled backup")
    overall_success = True
    error_details: list[str] = []

    # Step 1 — create local backup
    try:
        backup_file = await create_backup(db_path=db_path, backup_dir=backup_dir)
        logger.info("Backup created: %s", backup_file)
    except Exception as exc:
        logger.error("Backup creation failed: %s", exc, exc_info=exc)
        await _update_run_status(False, f"Backup creation failed: {exc}")
        if notify_on_failure:
            await _send_failure_email(str(exc))
        return

    # Step 2 — sync to destinations
    async with get_session() as db:
        result = await db.execute(
            select(BackupDestination).where(BackupDestination.enabled.is_(True))
        )
        destinations = list(result.scalars().all())

    if destinations:
        write_rclone_config(destinations)
        src_paths = [backup_dir]
        if include_uploads:
            src_paths.append(str(Path("data/uploads").resolve()))

        for dest in destinations:
            try:
                await sync_destination(dest, src_paths)
                logger.info("Synced to destination %s (%s)", dest.name, dest.type)
            except Exception as exc:
                overall_success = False
                msg = f"{dest.name}: {exc}"
                error_details.append(msg)
                logger.error("Sync failed for destination %s: %s", dest.name, exc)

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
            settings.backup_last_run_at = datetime.now(UTC).replace(tzinfo=None)
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
