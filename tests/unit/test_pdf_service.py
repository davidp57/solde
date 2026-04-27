"""Unit tests for pdf_service — mocks WeasyPrint to avoid the heavy import."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from backend.services.pdf_service import (
    generate_invoice_pdf,
    render_invoice_html,
    save_invoice_pdf,
)

# ---------------------------------------------------------------------------
# Minimal stubs matching the Jinja2 template expectations
# ---------------------------------------------------------------------------


@dataclass
class _InvoiceLine:
    description: str = "Cours de mathématiques"
    quantity: int = 4
    unit_price: Decimal = Decimal("25.00")
    amount: Decimal = Decimal("100.00")
    vat_rate: Decimal = Decimal("0.00")
    total: Decimal = Decimal("100.00")
    hours: int | None = None


@dataclass
class _FakeInvoice:
    number: str = "2024-001"
    reference: str | None = "REF-2024-001"
    description: str = "Soutien scolaire"
    date: date = field(default_factory=lambda: date(2024, 3, 1))
    due_date: date | None = field(default_factory=lambda: date(2024, 3, 31))
    total_amount: Decimal = Decimal("100.00")
    total_ht: Decimal = Decimal("100.00")
    total_ttc: Decimal = Decimal("100.00")
    total_vat: Decimal = Decimal("0.00")
    notes: str | None = None
    lines: list[Any] = field(default_factory=lambda: [_InvoiceLine()])


@dataclass
class _FakeSettings:
    association_name: str = "Association Éducation Plus"
    association_address: str | None = "10 rue de la Paix, 75001 Paris"
    association_siret: str | None = "12345678900001"
    association_logo_path: str | None = None
    email: str | None = "contact@edu-plus.fr"
    phone: str | None = "01 23 45 67 89"
    footer_text: str | None = "Merci pour votre confiance."
    iban: str | None = None


# ---------------------------------------------------------------------------
# render_invoice_html
# ---------------------------------------------------------------------------


def test_render_invoice_html_contains_invoice_number() -> None:
    html = render_invoice_html(_FakeInvoice(), "Alice Martin", _FakeSettings())
    assert "2024-001" in html


def test_render_invoice_html_contains_contact_name() -> None:
    html = render_invoice_html(_FakeInvoice(), "Alice Martin", _FakeSettings())
    assert "Alice Martin" in html


def test_render_invoice_html_contains_amount() -> None:
    html = render_invoice_html(_FakeInvoice(), "Alice Martin", _FakeSettings())
    # The template renders the total_ttc amount
    assert "100" in html


def test_render_invoice_html_contains_association_name() -> None:
    html = render_invoice_html(_FakeInvoice(), "Bob Dupont", _FakeSettings())
    assert "Association Éducation Plus" in html


def test_render_invoice_html_returns_string() -> None:
    result = render_invoice_html(_FakeInvoice(), "Alice Martin", _FakeSettings())
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_invoice_html_contains_reference() -> None:
    invoice = _FakeInvoice(reference="REF-TEST")
    html = render_invoice_html(invoice, "Alice Martin", _FakeSettings())
    assert "REF-TEST" in html


def test_render_invoice_html_contains_line_description() -> None:
    invoice = _FakeInvoice()
    html = render_invoice_html(invoice, "Alice Martin", _FakeSettings())
    assert "mathématiques" in html


def test_render_invoice_html_contains_contact_address() -> None:
    html = render_invoice_html(
        _FakeInvoice(), "Alice Martin", _FakeSettings(), "6 rue des Lilas\n57000 Metz"
    )
    assert "6 rue des Lilas" in html
    assert "57000 Metz" in html


def test_render_invoice_html_no_address_omitted() -> None:
    html = render_invoice_html(_FakeInvoice(), "Alice Martin", _FakeSettings(), None)
    # No address block should appear beyond the contact name
    assert "57000" not in html


# ---------------------------------------------------------------------------
# generate_invoice_pdf — WeasyPrint mocked via sys.modules to avoid
# loading native GTK libraries that may not be present on dev machines.
# ---------------------------------------------------------------------------


def _make_fake_weasyprint(pdf_bytes: bytes = b"%PDF-1.4 fake") -> MagicMock:
    """Return a fake weasyprint module where HTML().write_pdf() returns pdf_bytes."""
    mock_wp = MagicMock()
    mock_html_instance = MagicMock()
    mock_html_instance.write_pdf.return_value = pdf_bytes
    mock_wp.HTML.return_value = mock_html_instance
    return mock_wp


def test_generate_invoice_pdf_calls_weasyprint() -> None:
    import sys

    fake_wp = _make_fake_weasyprint(b"%PDF-1.4 fake")
    with patch.dict(sys.modules, {"weasyprint": fake_wp}):
        result = generate_invoice_pdf(_FakeInvoice(), "Alice Martin", _FakeSettings())

    assert result == b"%PDF-1.4 fake"
    fake_wp.HTML.return_value.write_pdf.assert_called_once()


def test_generate_invoice_pdf_passes_html_content() -> None:
    import sys

    fake_wp = _make_fake_weasyprint()
    with patch.dict(sys.modules, {"weasyprint": fake_wp}):
        generate_invoice_pdf(_FakeInvoice(), "Alice Martin", _FakeSettings())

    call_kwargs = fake_wp.HTML.call_args
    assert call_kwargs is not None
    html_string = call_kwargs.kwargs.get("string") or (
        call_kwargs.args[0] if call_kwargs.args else None
    )
    assert html_string is not None
    assert "2024-001" in html_string


def test_generate_invoice_pdf_returns_bytes() -> None:
    import sys

    fake_wp = _make_fake_weasyprint(b"%PDF-1.4")
    with patch.dict(sys.modules, {"weasyprint": fake_wp}):
        result = generate_invoice_pdf(_FakeInvoice(), "Alice Martin", _FakeSettings())

    assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# save_invoice_pdf
# ---------------------------------------------------------------------------


def test_save_invoice_pdf_creates_file(tmp_path: Path) -> None:
    pdf_bytes = b"%PDF-1.4 fake content"
    output_dir = str(tmp_path / "pdfs")
    result_path = save_invoice_pdf("2024-001", pdf_bytes, output_dir=output_dir)

    assert Path(result_path).exists()
    assert Path(result_path).read_bytes() == pdf_bytes


def test_save_invoice_pdf_sanitises_slash_in_number(tmp_path: Path) -> None:
    output_dir = str(tmp_path / "pdfs")
    result_path = save_invoice_pdf("2024/001", b"pdf", output_dir=output_dir)
    filename = Path(result_path).name
    assert "/" not in filename
    assert "\\" not in filename
    assert filename == "facture_2024-001.pdf"


def test_save_invoice_pdf_returns_path_string(tmp_path: Path) -> None:
    output_dir = str(tmp_path / "pdfs")
    result = save_invoice_pdf("INV-999", b"bytes", output_dir=output_dir)
    assert isinstance(result, str)
    assert "INV-999" in result
