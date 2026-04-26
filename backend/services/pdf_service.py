"""PDF generation service — uses WeasyPrint (lazy import for RAM constraint)."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def _template_env() -> Environment:
    template_dir = Path(__file__).parent.parent / "templates"
    return Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)


def render_invoice_html(
    invoice: object,
    contact_name: str,
    settings: object,
    contact_address: str | None = None,
) -> str:
    """Render the invoice Jinja2 template to an HTML string."""
    env = _template_env()
    template = env.get_template("invoice.html")
    return template.render(
        invoice=invoice,
        contact_name=contact_name,
        contact_address=contact_address,
        settings=settings,
    )


def generate_invoice_pdf(
    invoice: object,
    contact_name: str,
    settings: object,
    contact_address: str | None = None,
) -> bytes:
    """Generate a PDF from the invoice template.

    WeasyPrint is imported lazily to avoid loading ~50 MB at startup.
    """
    from weasyprint import HTML  # noqa: PLC0415

    html_content = render_invoice_html(invoice, contact_name, settings, contact_address)
    return bytes(HTML(string=html_content).write_pdf())


def save_invoice_pdf(
    invoice_number: str,
    pdf_bytes: bytes,
    output_dir: str = "data/pdfs",
) -> str:
    """Write PDF bytes to disk and return the relative file path."""
    safe_number = invoice_number.replace("/", "-").replace("\\", "-")
    output_path = Path(output_dir) / f"facture_{safe_number}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)
    return str(output_path)
