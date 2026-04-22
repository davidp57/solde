"""In-memory rate limiter for brute-force protection.

Designed for a single-worker Uvicorn deployment (Synology NAS target).
Tracks attempts per key (e.g. IP address) with a sliding time window.
"""

import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
    """Simple in-memory sliding-window rate limiter.

    Args:
        max_attempts: Maximum allowed attempts within the window.
        window_seconds: Duration of the sliding window in seconds.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_rate_limited(self, key: str) -> bool:
        """Return True if the key has exceeded the rate limit."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            attempts = self._attempts[key]
            # Prune expired entries
            self._attempts[key] = [t for t in attempts if t > cutoff]
            return len(self._attempts[key]) >= self.max_attempts

    def record_attempt(self, key: str) -> None:
        """Record a failed attempt for the given key."""
        now = time.monotonic()
        with self._lock:
            self._attempts[key].append(now)

    def reset(self, key: str) -> None:
        """Clear attempts for the given key (e.g. after successful login)."""
        with self._lock:
            self._attempts.pop(key, None)


# Singleton: 5 failed attempts per IP within 5 minutes
login_limiter = RateLimiter(max_attempts=5, window_seconds=300)
