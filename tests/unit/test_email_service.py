"""Unit tests for email_service — mocks smtplib to avoid real SMTP connections."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from backend.services.email_service import (
    EmailSendError,
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
    """Subject line must contain the invoice number and association name."""
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
