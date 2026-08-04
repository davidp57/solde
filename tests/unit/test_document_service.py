"""Unit tests for the document space."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.fiscal_year import FiscalYear, FiscalYearStatus
from backend.schemas.document import DocumentUpdate
from backend.services import document_service

PDF = b"%PDF-1.7\nminimal content"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep every test's files inside its own temporary directory."""
    monkeypatch.setattr(document_service, "DOCUMENTS_DIR", tmp_path / "documents")


async def _fiscal_year(db: AsyncSession, name: str = "2025") -> FiscalYear:
    fy = FiscalYear(
        name=name,
        start_date=date(2024, 8, 1),
        end_date=date(2025, 7, 31),
        status=FiscalYearStatus.CLOSED,
    )
    db.add(fy)
    await db.flush()
    return fy


class TestNormalizeTags:
    def test_case_spacing_and_duplicates_collapse(self) -> None:
        assert document_service.normalize_tags(
            ["AG", "ag", "  Assemblée   Générale ", "", "  "]
        ) == ["ag", "assemblée générale"]

    def test_parse_tags_reads_the_comma_separated_field(self) -> None:
        assert document_service.parse_tags("Statuts, AG , statuts") == ["statuts", "ag"]

    def test_none_yields_an_empty_list(self) -> None:
        assert document_service.normalize_tags(None) == []


class TestTypeDetection:
    @pytest.mark.parametrize(
        ("content", "filename", "expected"),
        [
            (PDF, "x.pdf", "application/pdf"),
            (PNG, "x.png", "image/png"),
            (b"\xff\xd8\xff\xe0abc", "x.jpg", "image/jpeg"),
            (b"RIFF\x00\x00\x00\x00WEBPmore", "x.webp", "image/webp"),
            (b"PK\x03\x04rest", "x.xlsx", "application/zip"),
            (b"nom;montant\nx;1", "x.csv", "text/csv"),
        ],
    )
    def test_accepted_formats(self, content: bytes, filename: str, expected: str) -> None:
        assert document_service.detect_mime_type(content, filename) == expected

    def test_executable_renamed_as_pdf_is_refused(self) -> None:
        with pytest.raises(document_service.DocumentError) as exc:
            document_service.detect_mime_type(b"MZ\x90\x00binary", "invoice.pdf")
        assert exc.value.code == "DOCUMENT_INVALID_TYPE"

    def test_binary_renamed_as_txt_is_refused(self) -> None:
        with pytest.raises(document_service.DocumentError):
            document_service.detect_mime_type(b"\x00\x01\x02\x03", "notes.txt")

    def test_empty_file_is_refused(self) -> None:
        with pytest.raises(document_service.DocumentError) as exc:
            document_service.detect_mime_type(b"", "x.pdf")
        assert exc.value.code == "DOCUMENT_EMPTY"


class TestStoreDocument:
    @pytest.mark.asyncio
    async def test_stores_metadata_and_file(self, db_session: AsyncSession) -> None:
        fy = await _fiscal_year(db_session)

        doc = await document_service.store_document(
            db_session,
            title="  Bilan 2025  ",
            filename="bilan.pdf",
            content=PDF,
            fiscal_year_id=fy.id,
            tags=["Comptabilité", "comptabilité", "AG"],
            notes="Signé",
            uploaded_by="david",
        )

        assert doc.title == "Bilan 2025"
        assert doc.mime_type == "application/pdf"
        assert doc.size_bytes == len(PDF)
        assert doc.tags == ["comptabilité", "ag"]
        assert doc.fiscal_year_name == "2025"
        assert doc.uploaded_by == "david"
        stored = await document_service.get_document_file(db_session, doc.id)
        assert stored is not None
        assert stored[0].is_file()
        assert stored[1] == "bilan.pdf"

    @pytest.mark.asyncio
    async def test_same_filename_twice_yields_distinct_files(
        self, db_session: AsyncSession
    ) -> None:
        first = await document_service.store_document(
            db_session, title="A", filename="scan.pdf", content=PDF
        )
        second = await document_service.store_document(
            db_session, title="B", filename="scan.pdf", content=PDF
        )

        paths = []
        for doc in (first, second):
            found = await document_service.get_document_file(db_session, doc.id)
            assert found is not None
            paths.append(found[0])
        assert paths[0] != paths[1]
        assert all(p.is_file() for p in paths)

    @pytest.mark.asyncio
    async def test_path_traversal_stays_inside_the_directory(
        self, db_session: AsyncSession
    ) -> None:
        doc = await document_service.store_document(
            db_session,
            title="Malicieux",
            filename="../../etc/passwd.pdf",
            content=PDF,
        )

        found = await document_service.get_document_file(db_session, doc.id)
        assert found is not None
        assert found[0].parent == document_service.DOCUMENTS_DIR
        assert found[1] == "passwd.pdf"

    @pytest.mark.asyncio
    async def test_refused_type_writes_nothing(self, db_session: AsyncSession) -> None:
        with pytest.raises(document_service.DocumentError):
            await document_service.store_document(
                db_session, title="X", filename="x.pdf", content=b"MZ\x90binary"
            )

        directory = document_service.DOCUMENTS_DIR
        assert not directory.exists() or not list(directory.iterdir())

    @pytest.mark.asyncio
    async def test_oversized_file_is_refused(self, db_session: AsyncSession) -> None:
        oversized = PDF + b"0" * document_service.MAX_DOCUMENT_BYTES
        with pytest.raises(document_service.DocumentError) as exc:
            await document_service.store_document(
                db_session, title="X", filename="x.pdf", content=oversized
            )
        assert exc.value.code == "FILE_TOO_LARGE"

    @pytest.mark.asyncio
    async def test_blank_title_is_refused(self, db_session: AsyncSession) -> None:
        with pytest.raises(document_service.DocumentError) as exc:
            await document_service.store_document(
                db_session, title="   ", filename="x.pdf", content=PDF
            )
        assert exc.value.code == "DOCUMENT_TITLE_REQUIRED"

    @pytest.mark.asyncio
    async def test_unknown_fiscal_year_is_refused(self, db_session: AsyncSession) -> None:
        with pytest.raises(document_service.DocumentError) as exc:
            await document_service.store_document(
                db_session, title="X", filename="x.pdf", content=PDF, fiscal_year_id=999
            )
        assert exc.value.code == "FISCAL_YEAR_NOT_FOUND"


class TestListing:
    @pytest.mark.asyncio
    async def test_filters_combine(self, db_session: AsyncSession) -> None:
        fy = await _fiscal_year(db_session)
        await document_service.store_document(
            db_session,
            title="Bilan 2025",
            filename="bilan.pdf",
            content=PDF,
            fiscal_year_id=fy.id,
            tags=["comptabilité"],
        )
        await document_service.store_document(
            db_session, title="Statuts", filename="statuts.pdf", content=PDF, tags=["juridique"]
        )

        by_year, total_year = await document_service.list_documents(
            db_session, fiscal_year_id=fy.id
        )
        assert [d.title for d in by_year] == ["Bilan 2025"]
        assert total_year == 1

        orphans, _ = await document_service.list_documents(db_session, without_fiscal_year=True)
        assert [d.title for d in orphans] == ["Statuts"]

        by_tag, _ = await document_service.list_documents(db_session, tag="Juridique")
        assert [d.title for d in by_tag] == ["Statuts"]

        by_search, _ = await document_service.list_documents(db_session, search="bila")
        assert [d.title for d in by_search] == ["Bilan 2025"]

        everything, total = await document_service.list_documents(db_session)
        assert len(everything) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_tags_are_listed_with_their_counts(self, db_session: AsyncSession) -> None:
        await document_service.store_document(
            db_session, title="A", filename="a.pdf", content=PDF, tags=["ag", "statuts"]
        )
        await document_service.store_document(
            db_session, title="B", filename="b.pdf", content=PDF, tags=["ag"]
        )

        tags = await document_service.list_tags(db_session)

        assert [(t.tag, t.count) for t in tags] == [("ag", 2), ("statuts", 1)]


class TestUpdateAndDelete:
    @pytest.mark.asyncio
    async def test_update_normalizes_tags_and_detaches_the_year(
        self, db_session: AsyncSession
    ) -> None:
        fy = await _fiscal_year(db_session)
        doc = await document_service.store_document(
            db_session, title="A", filename="a.pdf", content=PDF, fiscal_year_id=fy.id
        )

        updated = await document_service.update_document(
            db_session,
            doc.id,
            DocumentUpdate(title="Assemblée 2025", fiscal_year_id=None, tags=["  AG  ", "ag"]),
        )

        assert updated is not None
        assert updated.title == "Assemblée 2025"
        assert updated.fiscal_year_id is None
        assert updated.fiscal_year_name is None
        assert updated.tags == ["ag"]

    @pytest.mark.asyncio
    async def test_delete_removes_row_and_file(self, db_session: AsyncSession) -> None:
        doc = await document_service.store_document(
            db_session, title="A", filename="a.pdf", content=PDF
        )
        found = await document_service.get_document_file(db_session, doc.id)
        assert found is not None
        path = found[0]

        assert await document_service.delete_document(db_session, doc.id) is True

        assert not path.exists()
        assert await document_service.get_document(db_session, doc.id) is None

    @pytest.mark.asyncio
    async def test_delete_succeeds_when_the_file_is_already_gone(
        self, db_session: AsyncSession
    ) -> None:
        doc = await document_service.store_document(
            db_session, title="A", filename="a.pdf", content=PDF
        )
        found = await document_service.get_document_file(db_session, doc.id)
        assert found is not None
        found[0].unlink()

        assert await document_service.delete_document(db_session, doc.id) is True
        assert await document_service.get_document(db_session, doc.id) is None

    @pytest.mark.asyncio
    async def test_unknown_document_is_reported_not_raised(self, db_session: AsyncSession) -> None:
        assert await document_service.delete_document(db_session, 999) is False
        assert await document_service.get_document(db_session, 999) is None
        assert await document_service.get_document_file(db_session, 999) is None
