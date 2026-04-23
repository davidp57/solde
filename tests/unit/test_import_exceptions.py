"""Tests for typed import exceptions (BL-058)."""

from __future__ import annotations

import pytest


class TestExceptionHierarchy:
    """Verify that custom import exceptions exist and inherit correctly."""

    def test_import_file_open_error_exists(self) -> None:
        from backend.services.excel_import._exceptions import ImportFileOpenError

        assert issubclass(ImportFileOpenError, Exception)

    def test_import_sheet_error_exists(self) -> None:
        from backend.services.excel_import._exceptions import ImportSheetError

        assert issubclass(ImportSheetError, Exception)

    def test_import_sheet_error_stores_sheet_name(self) -> None:
        from backend.services.excel_import._exceptions import ImportSheetError

        exc = ImportSheetError("boom", sheet_name="Factures")
        assert exc.sheet_name == "Factures"
        assert "boom" in str(exc)

    def test_import_file_open_error_stores_file_name(self) -> None:
        from backend.services.excel_import._exceptions import ImportFileOpenError

        exc = ImportFileOpenError("bad file", file_name="Gestion 2025.xlsx")
        assert exc.file_name == "Gestion 2025.xlsx"
        assert "bad file" in str(exc)

    def test_import_sheet_failure_is_import_sheet_error(self) -> None:
        """_ImportSheetFailure should now be an alias for ImportSheetError."""
        from backend.services.excel_import._constants import _ImportSheetFailure
        from backend.services.excel_import._exceptions import ImportSheetError

        assert _ImportSheetFailure is ImportSheetError

    def test_exceptions_importable_from_package(self) -> None:
        """Both exceptions should be importable from the package root."""
        from backend.services.excel_import import (
            ImportFileOpenError,
            ImportSheetError,
        )

        assert issubclass(ImportFileOpenError, Exception)
        assert issubclass(ImportSheetError, Exception)


class TestOrchestratorUsesTypedExceptions:
    """Verify that the orchestrator raises typed exceptions."""

    @pytest.mark.asyncio
    async def test_import_gestion_file_open_error(self, db_session) -> None:
        """A corrupt file should produce an ImportFileOpenError-related error in the result."""
        from backend.services.excel_import import import_gestion_file

        result = await import_gestion_file(db_session, b"not-a-valid-xlsx", "bad.xlsx")
        assert result.errors
        # The error message should mention file opening
        assert any(
            "ouverture" in e.lower() or "open" in e.lower() or "file" in e.lower()
            for e in result.errors
        )

    @pytest.mark.asyncio
    async def test_import_comptabilite_file_open_error(self, db_session) -> None:
        """A corrupt file should produce an error in the result."""
        from backend.services.excel_import import import_comptabilite_file

        result = await import_comptabilite_file(db_session, b"not-a-valid-xlsx", "bad.xlsx")
        assert result.errors


class TestPreviewUsesTypedExceptions:
    """Verify that preview functions handle file open errors gracefully."""

    @pytest.mark.asyncio
    async def test_preview_gestion_corrupt_file(self, db_session) -> None:
        from backend.services.excel_import import preview_gestion_file

        preview = await preview_gestion_file(db_session, b"corrupt-data", "bad.xlsx")
        assert preview.errors

    @pytest.mark.asyncio
    async def test_preview_comptabilite_corrupt_file(self, db_session) -> None:
        from backend.services.excel_import import preview_comptabilite_file

        preview = await preview_comptabilite_file(db_session, b"corrupt-data", "bad.xlsx")
        assert preview.errors
