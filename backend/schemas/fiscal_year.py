"""Pydantic schemas for fiscal years."""

from __future__ import annotations

from datetime import date as _Date

from pydantic import BaseModel, field_validator

from backend.models.fiscal_year import FiscalYearStatus


class FiscalYearCreate(BaseModel):
    name: str
    start_date: _Date
    end_date: _Date

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: _Date, info: object) -> _Date:
        # info.data may not have start_date if validation already failed
        data = getattr(info, "data", {})
        start = data.get("start_date")
        if start is not None and v <= start:
            raise ValueError("end_date must be after start_date")
        return v


class FiscalYearRead(BaseModel):
    id: int
    name: str
    start_date: _Date
    end_date: _Date
    status: FiscalYearStatus

    model_config = {"from_attributes": True}
