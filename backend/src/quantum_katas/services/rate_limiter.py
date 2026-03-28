"""Simple in-memory rate limiter for API endpoints.

Uses a sliding window approach with per-IP tracking.
Not suitable for multi-process deployments (use Redis-based limiter instead).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict

# Maximum requests per window
MAX_REQUESTS = 30
# Window duration in seconds
WINDOW_SECONDS = 60


class RateLimiter:
    """Thread-safe in-memory rate limiter using a sliding window."""

    def __init__(self, max_requests: int = MAX_REQUESTS, window_seconds: int = WINDOW_SECONDS) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """Check if a request from the given client is allowed.

        Returns True if the request is within rate limits, False otherwise.
        """
        now = time.monotonic()
        cutoff = now - self._window_seconds

        with self._lock:
            timestamps = self._requests[client_id]
            # Remove expired timestamps
            self._requests[client_id] = [ts for ts in timestamps if ts > cutoff]
            timestamps = self._requests[client_id]

            if len(timestamps) >= self._max_requests:
                return False

            timestamps.append(now)
            return True


# Global rate limiter instance
rate_limiter = RateLimiter()
