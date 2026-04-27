"""Unit tests for email_service — mocks smtplib to avoid real SMTP connections."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from backend.services.email_service import (
    EmailSendError,
    compose_body,
    compose_subject,
    send_invoice_email,
)

# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

_COMMON_KWARGS: dict = {
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "smtp_user": "user@example.com",
    "smtp_password": "secret",
    "smtp_from_email": "factures@asso.fr",
    "smtp_use_tls": True,
    "recipient_email": "client@example.com",
    "invoice_number": "2024-001",
    "association_name": "Association Test",
    "pdf_bytes": b"%PDF-fake",
}


# ---------------------------------------------------------------------------
# Successful sends
# ---------------------------------------------------------------------------


def test_send_invoice_email_starttls_success() -> None:
    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_invoice_email(**_COMMON_KWARGS)

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=30)


def test_send_invoice_email_ssl_success() -> None:
    kwargs = {**_COMMON_KWARGS, "smtp_use_tls": False, "smtp_port": 465}
    mock_server = MagicMock()
    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_cls:
        mock_smtp_ssl_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_ssl_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_invoice_email(**kwargs)

    mock_smtp_ssl_cls.assert_called_once_with("smtp.example.com", 465, timeout=30)


def test_send_invoice_email_with_bcc() -> None:
    """BCC field must be set in the message headers when provided."""
    sent_messages: list = []

    class _FakeSMTP:
        def __enter__(self) -> _FakeSMTP:
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def ehlo(self) -> None:
            pass

        def starttls(self, **kwargs: object) -> None:
            pass

        def login(self, user: str, password: str) -> None:
            pass

        def send_message(self, msg: object) -> None:
            sent_messages.append(msg)

    with patch("smtplib.SMTP", return_value=_FakeSMTP()):
        send_invoice_email(**{**_COMMON_KWARGS, "bcc": "archivage@asso.fr"})

    assert sent_messages, "send_message was not called"
    assert sent_messages[0]["Bcc"] == "archivage@asso.fr"


def test_send_invoice_email_without_bcc() -> None:
    """Bcc header must be absent when bcc is None."""
    sent_messages: list = []

    class _FakeSMTP:
        def __enter__(self) -> _FakeSMTP:
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def ehlo(self) -> None:
            pass

        def starttls(self, **kwargs: object) -> None:
            pass

        def login(self, user: str, password: str) -> None:
            pass

        def send_message(self, msg: object) -> None:
            sent_messages.append(msg)

    with patch("smtplib.SMTP", return_value=_FakeSMTP()):
        send_invoice_email(**{**_COMMON_KWARGS, "bcc": None})

    assert sent_messages
    assert sent_messages[0]["Bcc"] is None


def test_send_invoice_email_message_subject() -> None:
    """Without description, subject contains invoice number and association name."""
    sent_messages: list = []

    class _FakeSMTP:
        def __enter__(self) -> _FakeSMTP:
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def ehlo(self) -> None:
            pass

        def starttls(self, **kwargs: object) -> None:
            pass

        def login(self, user: str, password: str) -> None:
            pass

        def send_message(self, msg: object) -> None:
            sent_messages.append(msg)

    with patch("smtplib.SMTP", return_value=_FakeSMTP()):
        send_invoice_email(**_COMMON_KWARGS)

    assert sent_messages
    subject = sent_messages[0]["Subject"]
    assert "2024-001" in subject
    assert "Association Test" in subject


def test_send_invoice_email_subject_with_description() -> None:
    """With description, subject and body contain invoice number and description."""
    sent_messages: list = []

    class _FakeSMTP:
        def __enter__(self) -> _FakeSMTP:
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def ehlo(self) -> None:
            pass

        def starttls(self, **kwargs: object) -> None:
            pass

        def login(self, user: str, password: str) -> None:
            pass

        def send_message(self, msg: object) -> None:
            sent_messages.append(msg)

    with patch("smtplib.SMTP", return_value=_FakeSMTP()):
        send_invoice_email(**{**_COMMON_KWARGS, "description": "cours du mois d'avril 2026"})

    assert sent_messages
    subject = sent_messages[0]["Subject"]
    assert "2024-001" in subject
    assert "cours du mois d'avril 2026" in subject
    assert "Association Test" not in subject

    # Description must also appear in the email body
    body_part = sent_messages[0].get_payload(0)
    body_text = body_part.get_payload(decode=True).decode()
    assert "cours du mois d'avril 2026" in body_text


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_send_invoice_email_raises_email_send_error_on_smtp_exception() -> None:
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__ = MagicMock(
            side_effect=smtplib.SMTPConnectError(421, "Service unavailable")
        )
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        with pytest.raises(EmailSendError):
            send_invoice_email(**_COMMON_KWARGS)


def test_send_invoice_email_raises_email_send_error_on_os_error() -> None:
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.side_effect = OSError("Connection refused")
        with pytest.raises(EmailSendError):
            send_invoice_email(**_COMMON_KWARGS)


def test_send_invoice_email_raises_email_send_error_on_auth_failure() -> None:
    class _FakeSMTP:
        def __enter__(self) -> _FakeSMTP:
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def ehlo(self) -> None:
            pass

        def starttls(self, **kwargs: object) -> None:
            pass

        def login(self, user: str, password: str) -> None:
            raise smtplib.SMTPAuthenticationError(535, b"Authentication failed")

        def send_message(self, msg: object) -> None:
            pass

    with patch("smtplib.SMTP", return_value=_FakeSMTP()), pytest.raises(EmailSendError):
        send_invoice_email(**_COMMON_KWARGS)


# ---------------------------------------------------------------------------
# compose_subject helper
# ---------------------------------------------------------------------------


def test_compose_subject_without_description() -> None:
    result = compose_subject("2024-001", None, "Mon Asso")
    assert "2024-001" in result
    assert "Mon Asso" in result


def test_compose_subject_with_description() -> None:
    result = compose_subject("2024-001", "cours d'avril", "Mon Asso")
    assert "2024-001" in result
    assert "cours d'avril" in result
    assert "Mon Asso" not in result


def test_compose_subject_with_template() -> None:
    result = compose_subject(
        "2024-001", "cours d'avril", "Mon Asso", template="Ref: {invoice_number}"
    )
    assert result == "Ref: 2024-001"


def test_compose_subject_with_template_invoice_ref() -> None:
    result = compose_subject("2024-001", "cours d'avril", "Mon Asso", template="Fact {invoice_ref}")
    assert result == "Fact 2024-001 — cours d'avril"


def test_compose_subject_with_template_no_description() -> None:
    result = compose_subject("2024-001", None, "Mon Asso", template="Fact {invoice_ref}")
    assert result == "Fact 2024-001"


# ---------------------------------------------------------------------------
# compose_body helper
# ---------------------------------------------------------------------------


def test_compose_body_without_description() -> None:
    result = compose_body("2024-001", None, "Mon Asso")
    assert "2024-001" in result
    assert "Mon Asso" in result


def test_compose_body_with_description() -> None:
    result = compose_body("2024-001", "cours d'avril", "Mon Asso")
    assert "2024-001" in result
    assert "cours d'avril" in result


def test_compose_body_with_template() -> None:
    tpl = "Bonjour,\n\nFacture {invoice_number} - {description}.\n\n{association_name}"
    result = compose_body("2024-001", "cours d'avril", "Mon Asso", template=tpl)
    assert "2024-001" in result
    assert "cours d'avril" in result
    assert "Mon Asso" in result


def test_compose_body_with_template_unknown_var() -> None:
    """Unknown variables in the template are kept as-is (safe format_map)."""
    tpl = "Facture {invoice_number} {unknown_var}"
    result = compose_body("2024-001", None, "Mon Asso", template=tpl)
    assert "{unknown_var}" in result


# ---------------------------------------------------------------------------
# override_subject / override_body
# ---------------------------------------------------------------------------


def test_send_invoice_email_override_subject_and_body() -> None:
    """When override_subject/override_body are provided, they are used verbatim."""
    sent_messages: list = []

    class _FakeSMTP:
        def __enter__(self) -> _FakeSMTP:
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def ehlo(self) -> None:
            pass

        def starttls(self, **kwargs: object) -> None:
            pass

        def login(self, user: str, password: str) -> None:
            pass

        def send_message(self, msg: object) -> None:
            sent_messages.append(msg)

    with patch("smtplib.SMTP", return_value=_FakeSMTP()):
        send_invoice_email(
            **_COMMON_KWARGS,
            override_subject="Sujet personnalisé",
            override_body="Corps personnalisé",
        )

    assert sent_messages
    assert sent_messages[0]["Subject"] == "Sujet personnalisé"
    body_text = sent_messages[0].get_payload(0).get_payload(decode=True).decode()
    assert "Corps personnalisé" in body_text
