"""Email service — sends invoice PDFs via SMTP (stdlib smtplib)."""

import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TypedDict


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


# --- Reminder (dunning) emails -------------------------------------------------
# Distinct from the initial invoice send. Two variants are selected from the
# reminder history: "first" (never reminded) and "next" (already reminded).

_DEFAULT_REMINDER_FIRST_SUBJECT = "Rappel — facture {invoice_ref} en attente de règlement"
_DEFAULT_REMINDER_FIRST_BODY = (
    "Bonjour,\n\n"
    "Sauf erreur de notre part, la facture {invoice_ref} d'un montant de {montant_du} € "
    "(échéance du {echeance}) demeure impayée à ce jour.\n\n"
    "Nous vous remercions de bien vouloir procéder à son règlement.\n\n"
    "Cordialement,\n{association_name}"
)
_DEFAULT_REMINDER_NEXT_SUBJECT = "Nouvelle relance — facture {invoice_ref} impayée"
_DEFAULT_REMINDER_NEXT_BODY = (
    "Bonjour,\n\n"
    "Malgré notre précédent rappel (dernière relance le {derniere_relance}), la facture "
    "{invoice_ref} d'un montant de {montant_du} € (échéance du {echeance}) reste impayée.\n\n"
    "Nous vous remercions de régulariser votre situation dans les meilleurs délais.\n\n"
    "Cordialement,\n{association_name}"
)


def _reminder_format(
    template: str,
    *,
    invoice_number: str,
    description: str | None,
    association_name: str,
    amount_due: str,
    due_date: str,
    last_reminder: str,
    reminder_count: int,
) -> str:
    invoice_ref = f"{invoice_number} — {description}" if description else invoice_number
    return template.format_map(
        _SafeFormatMap(
            invoice_number=invoice_number,
            description=description or "",
            association_name=association_name,
            invoice_ref=invoice_ref,
            montant_du=amount_due,
            echeance=due_date,
            derniere_relance=last_reminder,
            nombre_de_relances=reminder_count,
        )
    )


def compose_reminder(
    *,
    reminder_count: int,
    invoice_number: str,
    description: str | None,
    association_name: str,
    amount_due: str,
    due_date: str,
    last_reminder: str,
    first_subject_template: str | None = None,
    first_body_template: str | None = None,
    next_subject_template: str | None = None,
    next_body_template: str | None = None,
) -> tuple[str, str]:
    """Compose a reminder ``(subject, body)`` for an overdue invoice.

    ``reminder_count`` is the number of reminders already sent (0 → first
    reminder, ≥1 → follow-up). The matching configured template is used, or a
    built-in default when it is ``None``/empty. Reminder variables
    (``{montant_du}``, ``{echeance}``, ``{derniere_relance}``,
    ``{nombre_de_relances}``) and the invoice variables of the initial email are
    available; unknown keys are left as-is.
    """
    is_first = reminder_count == 0
    if is_first:
        subject_tpl = first_subject_template or _DEFAULT_REMINDER_FIRST_SUBJECT
        body_tpl = first_body_template or _DEFAULT_REMINDER_FIRST_BODY
    else:
        subject_tpl = next_subject_template or _DEFAULT_REMINDER_NEXT_SUBJECT
        body_tpl = next_body_template or _DEFAULT_REMINDER_NEXT_BODY

    def _fmt(template: str) -> str:
        return _reminder_format(
            template,
            invoice_number=invoice_number,
            description=description,
            association_name=association_name,
            amount_due=amount_due,
            due_date=due_date,
            last_reminder=last_reminder,
            reminder_count=reminder_count,
        )

    return _fmt(subject_tpl), _fmt(body_tpl)


def send_invoice_email(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from_email: str,
    smtp_use_tls: bool,
    recipient_email: str | list[str],
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
    recipients_list = recipient_email if isinstance(recipient_email, list) else [recipient_email]
    msg["From"] = smtp_from_email
    msg["To"] = ", ".join(recipients_list)
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


def send_plain_email(
    *,
    host: str,
    port: int,
    user: str | None,
    password: str | None,
    use_tls: bool,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
) -> None:
    """Send a plain-text email (no attachment).

    Used for system notifications such as backup failure alerts.
    Raises EmailSendError if delivery fails.
    """
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        if use_tls:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.ehlo()
                server.starttls(context=ctx)
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailSendError(f"Failed to send plain email: {exc}") from exc


class BulkEmailMessage(TypedDict):
    to: str
    cc: list[str]
    subject: str
    body: str
    ref: int


class BulkEmailFailure(TypedDict):
    ref: int
    error: str


def send_bulk_emails(
    *,
    host: str,
    port: int,
    user: str | None,
    password: str | None,
    use_tls: bool,
    from_email: str,
    messages: list[BulkEmailMessage],
) -> list[BulkEmailFailure]:
    """Send many plain-text emails over a **single** SMTP connection.

    Each message is sent to ``to`` with ``cc`` in copy. ``ref`` is echoed back
    on failure so the caller can map it to a contact.

    Returns the list of per-message failures. Raises EmailConfigError if the
    host is missing, EmailSendError if the connection (or login) itself fails.
    """
    if not host:
        raise EmailConfigError("SMTP host is not configured")

    failures: list[BulkEmailFailure] = []
    try:
        if use_tls:
            ctx = ssl.create_default_context()
            server = smtplib.SMTP(host, port, timeout=30)
            server.ehlo()
            server.starttls(context=ctx)
        else:
            server = smtplib.SMTP(host, port, timeout=30)
        with server:
            if user and password:
                server.login(user, password)
            for message in messages:
                to_email = message["to"]
                cc_list = list(message["cc"])
                msg = MIMEMultipart()
                msg["From"] = from_email
                msg["To"] = to_email
                if cc_list:
                    msg["Cc"] = ", ".join(cc_list)
                msg["Subject"] = message["subject"]
                msg.attach(MIMEText(message["body"], "plain", "utf-8"))
                try:
                    server.send_message(msg, to_addrs=[to_email, *cc_list])
                except smtplib.SMTPException as exc:
                    failures.append({"ref": message["ref"], "error": str(exc)})
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailSendError(f"SMTP connection failed: {exc}") from exc

    return failures
