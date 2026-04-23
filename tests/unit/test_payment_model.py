"""Unit tests for BL-065 — Payment model must not use __allow_unmapped__."""

from __future__ import annotations

from backend.models.payment import Payment


def test_payment_model_has_no_allow_unmapped() -> None:
    """Payment model must not carry __allow_unmapped__ = True."""
    assert not getattr(Payment, "__allow_unmapped__", False)


def test_payment_model_has_no_invoice_number_class_attr() -> None:
    """invoice_number is a DTO-only field, not a class-level attribute on Payment."""
    assert "invoice_number" not in {c.key for c in Payment.__mapper__.columns}
    assert not hasattr(Payment, "invoice_number")


def test_payment_model_has_no_invoice_type_class_attr() -> None:
    """invoice_type is a DTO-only field, not a class-level attribute on Payment."""
    assert "invoice_type" not in {c.key for c in Payment.__mapper__.columns}
    assert not hasattr(Payment, "invoice_type")
