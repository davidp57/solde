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
) -> None:
    """Send an invoice PDF by email.

    Raises EmailSendError if delivery fails.
    """
    msg = MIMEMultipart()
    msg["From"] = smtp_from_email
    msg["To"] = recipient_email
    msg["Subject"] = f"Facture {invoice_number} — {association_name}"

    body = (
        f"Bonjour,\n\n"
        f"Veuillez trouver ci-joint votre facture {invoice_number}.\n\n"
        f"Cordialement,\n{association_name}"
    )
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
                server.sendmail(smtp_from_email, recipient_email, msg.as_string())
        else:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from_email, recipient_email, msg.as_string())
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailSendError(f"Failed to send email: {exc}") from exc
