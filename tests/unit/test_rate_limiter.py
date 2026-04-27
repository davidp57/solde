"""Unit tests for the in-memory rate limiter."""

import time
from unittest.mock import patch

from backend.services.rate_limiter import RateLimiter


def test_allows_requests_below_limit() -> None:
    limiter = RateLimiter(max_attempts=3, window_seconds=60)
    for _ in range(3):
        assert not limiter.is_rate_limited("ip1")
        limiter.record_attempt("ip1")
    # 4th should be blocked
    assert limiter.is_rate_limited("ip1")


def test_different_keys_are_independent() -> None:
    limiter = RateLimiter(max_attempts=2, window_seconds=60)
    limiter.record_attempt("ip1")
    limiter.record_attempt("ip1")
    assert limiter.is_rate_limited("ip1")
    assert not limiter.is_rate_limited("ip2")


def test_reset_clears_attempts() -> None:
    limiter = RateLimiter(max_attempts=2, window_seconds=60)
    limiter.record_attempt("ip1")
    limiter.record_attempt("ip1")
    assert limiter.is_rate_limited("ip1")
    limiter.reset("ip1")
    assert not limiter.is_rate_limited("ip1")


def test_expired_attempts_are_pruned() -> None:
    limiter = RateLimiter(max_attempts=2, window_seconds=10)
    base = time.monotonic()
    with patch("time.monotonic", return_value=base):
        limiter.record_attempt("ip1")
        limiter.record_attempt("ip1")
    # Advance past the window
    with patch("time.monotonic", return_value=base + 11):
        assert not limiter.is_rate_limited("ip1")
