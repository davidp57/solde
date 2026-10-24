"""The application engine must never write bound parameter values to the logs."""

import logging

import pytest
from sqlalchemy import text

from backend.database import _build_engine

_SECRET = "smtp-password-must-not-be-logged"


@pytest.mark.asyncio
async def test_engine_logs_statements_without_bound_parameters(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Production routes ``sqlalchemy.engine`` to the log file at DEBUG, which makes
    SQLAlchemy log every statement even with ``echo=False``; values such as the SMTP
    password or the chat API key must not travel with them."""
    # backend.main sets propagate=False on this logger: listen on it directly.
    sa_logger = logging.getLogger("sqlalchemy.engine")
    sa_logger.addHandler(caplog.handler)
    engine = _build_engine("sqlite+aiosqlite:///:memory:")
    try:
        with caplog.at_level(logging.INFO, logger="sqlalchemy.engine"):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT :value"), {"value": _SECRET})
    finally:
        await engine.dispose()
        sa_logger.removeHandler(caplog.handler)

    assert "SELECT ?" in caplog.text
    assert _SECRET not in caplog.text
