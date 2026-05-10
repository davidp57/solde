"""Standardised API error helpers.

Every HTTP error returned by Solde uses a structured JSON body::

    {"code": "MACHINE_READABLE_CODE", "detail": "Human-readable English message"}

The frontend maps ``code`` to a translated i18n string for display.
"""

from __future__ import annotations

from fastapi import HTTPException, status


def api_error(
    status_code: int,
    code: str,
    detail: str,
) -> HTTPException:
    """Build a structured HTTPException with a machine-readable code."""
    return HTTPException(status_code=status_code, detail={"code": code, "detail": detail})


# ---------------------------------------------------------------------------
# Common reusable error factories
# ---------------------------------------------------------------------------


def not_found(resource: str) -> HTTPException:
    """404 error for a missing resource."""
    normalized = resource.upper().replace(" ", "_").replace("-", "_")
    code = f"{normalized}_NOT_FOUND"
    return api_error(status.HTTP_404_NOT_FOUND, code, f"{resource} not found")


def conflict(code: str, detail: str) -> HTTPException:
    """409 Conflict."""
    return api_error(status.HTTP_409_CONFLICT, code, detail)


def unprocessable(code: str, detail: str) -> HTTPException:
    """422 Unprocessable Entity."""
    return api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, code, detail)
