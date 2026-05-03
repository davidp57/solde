"""In-memory rate limiter for brute-force protection.

Designed for a single-worker Uvicorn deployment (Synology NAS target).
Tracks attempts per key (e.g. IP address) with a sliding time window.
"""

import time
from collections import defaultdict
from threading import Lock

# Purge stale keys every N record_attempt calls to prevent unbounded dict growth
_PURGE_INTERVAL = 100


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
        self._calls_since_purge = 0

    def is_rate_limited(self, key: str) -> bool:
        """Return True if the key has exceeded the rate limit."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            attempts = self._attempts[key]
            # Prune expired entries for this key
            self._attempts[key] = [t for t in attempts if t > cutoff]
            # Trigger global purge periodically so stale keys from quiet periods are cleaned up
            self._calls_since_purge += 1
            if self._calls_since_purge >= _PURGE_INTERVAL:
                self._purge_stale(now)
                self._calls_since_purge = 0
            return len(self._attempts[key]) >= self.max_attempts

    def record_attempt(self, key: str) -> None:
        """Record a failed attempt for the given key."""
        now = time.monotonic()
        with self._lock:
            self._attempts[key].append(now)
            self._calls_since_purge += 1
            if self._calls_since_purge >= _PURGE_INTERVAL:
                self._purge_stale(now)
                self._calls_since_purge = 0

    def reset(self, key: str) -> None:
        """Clear attempts for the given key (e.g. after successful login)."""
        with self._lock:
            self._attempts.pop(key, None)

    def _purge_stale(self, now: float) -> None:
        """Remove keys whose entire attempt list has expired. Must be called under lock."""
        cutoff = now - self.window_seconds
        stale = [k for k, v in self._attempts.items() if all(t <= cutoff for t in v)]
        for k in stale:
            del self._attempts[k]


# Singleton: 5 failed attempts per IP within 5 minutes
login_limiter = RateLimiter(max_attempts=5, window_seconds=300)
