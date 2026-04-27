"""Custom SQLAlchemy column type decorators."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import Numeric
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class DecimalType(TypeDecorator[Decimal]):
    """Numeric column that always returns :class:`Decimal` (never :class:`float`) from SQLite.

    SQLite stores NUMERIC columns as floating-point; this decorator wraps the
    result so that every read returns a proper :class:`Decimal`, preventing
    subtle binary rounding errors in monetary arithmetic.
    """

    impl = Numeric
    cache_ok = True

    def process_result_value(self, value: Any, dialect: Dialect) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
