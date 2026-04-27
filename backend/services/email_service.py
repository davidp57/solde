"""Email service — sends invoice PDFs via SMTP (stdlib smtplib)."""

import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailConfigError(Exception):
    """Raised when SMTP is not configured."""


class EmailSendError(Exception):
    """Raised when the email cannot be sent."""


def compose_subject(
    invoice_number: str,
    description: str | None,
    association_name: str,
    template: str | None = None,
) -> str:
    """Return the email subject for an invoice.

    If *template* is provided it is formatted with these variables:
    - ``{invoice_number}`` — the invoice number
    - ``{description}``   — the invoice description (empty string when absent)
    - ``{association_name}`` — the association name
    - ``{invoice_ref}``   — ``{invoice_number} — {description}`` when description
                            is set, otherwise just ``{invoice_number}``

    Unknown keys are left as-is (safe substitution).
    """
    if template:
        invoice_ref = f"{invoice_number} — {description}" if description else invoice_number
        return template.format_map(
            _SafeFormatMap(
                invoice_number=invoice_number,
                description=description or "",
                association_name=association_name,
                invoice_ref=invoice_ref,
            )
        )
    if description:
        return f"Facture {invoice_number} — {description}"
    return f"Facture {invoice_number} — {association_name}"


def compose_body(
    invoice_number: str,
    description: str | None,
    association_name: str,
    template: str | None = None,
) -> str:
    """Return the email body for an invoice.

    Supports the same template variables as :func:`compose_subject`.
    """
    if template:
        invoice_ref = f"{invoice_number} — {description}" if description else invoice_number
        return template.format_map(
            _SafeFormatMap(
                invoice_number=invoice_number,
                description=description or "",
                association_name=association_name,
                invoice_ref=invoice_ref,
            )
        )
    invoice_ref = f"{invoice_number} — {description}" if description else invoice_number
    return (
        f"Bonjour,\n\n"
        f"Veuillez trouver ci-joint votre facture {invoice_ref}.\n\n"
        f"Cordialement,\n{association_name}"
    )


class _SafeFormatMap(dict):  # type: ignore[type-arg]
    """dict subclass that returns ``{key}`` for missing keys instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


def send_invoice_email(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from_email: str,
    smtp_use_tls: bool,
    recipient_email: str,
    invoice_number: str,
    association_name: str,
    pdf_bytes: bytes,
    bcc: str | None = None,
    description: str | None = None,
    override_subject: str | None = None,
    override_body: str | None = None,
) -> None:
    """Send an invoice PDF by email.

    If override_subject / override_body are provided they take precedence over
    the automatically composed defaults (used when the user edits before sending).

    Raises EmailSendError if delivery fails.
    """
    subject = override_subject or compose_subject(invoice_number, description, association_name)
    body = override_body or compose_body(invoice_number, description, association_name)

    msg = MIMEMultipart()
    msg["From"] = smtp_from_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    if bcc:
        msg["Bcc"] = bcc

    msg.attach(MIMEText(body, "plain", "utf-8"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=f"facture_{invoice_number}.pdf",
    )
    msg.attach(attachment)

    try:
        if smtp_use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailSendError(f"Failed to send email: {exc}") from exc
