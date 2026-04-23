"""Typed exceptions for the Excel import service."""

from __future__ import annotations


class ImportFileOpenError(Exception):
    """Raised when an Excel file cannot be opened or parsed by openpyxl."""

    def __init__(self, message: str, *, file_name: str | None = None) -> None:
        super().__init__(message)
        self.file_name = file_name


class ImportSheetError(Exception):
    """Raised when a sheet-level import operation fails (flush, constraint, etc.)."""

    def __init__(self, message: str, *, sheet_name: str | None = None) -> None:
        super().__init__(message)
        self.sheet_name = sheet_name
