"""Code execution router with in-memory rate limiting."""

from __future__ import annotations

import asyncio
import threading
import time
import uuid

from fastapi import APIRouter, HTTPException, Request

from quantum_katas.models.execution import ExecutionRequest, ExecutionResult
from quantum_katas.services.executor import execute_code

router = APIRouter()

# ---------------------------------------------------------------------------
# M-1: Simple in-memory sliding-window rate limiter (30 requests/minute/IP)
# ---------------------------------------------------------------------------
_RATE_LIMIT_WINDOW_SECONDS: int = 60
_RATE_LIMIT_MAX_REQUESTS: int = 30

# Prune stale IP entries after this many seconds of inactivity.
# Prevents unbounded growth when many unique IPs make one-off requests.
_RATE_LIMIT_EVICTION_SECONDS: int = _RATE_LIMIT_WINDOW_SECONDS * 2  # 2 minutes

_rate_limit_store: dict[str, list[float]] = {}
_rate_limit_lock = threading.Lock()


def _is_rate_limited(client_ip: str) -> tuple[bool, int]:
    """Return (is_limited, retry_after_seconds) for *client_ip*.

    Also evicts stale IP entries whose last timestamp is older than
    _RATE_LIMIT_EVICTION_SECONDS to prevent unbounded dict growth.
    """
    now = time.monotonic()
    cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
    eviction_cutoff = now - _RATE_LIMIT_EVICTION_SECONDS

    with _rate_limit_lock:
        # Evict IPs whose most recent request is older than the eviction window.
        # This prevents memory growth from one-off requests by unique IPs.
        stale_ips = [
            ip for ip, timestamps in _rate_limit_store.items() if not timestamps or timestamps[-1] < eviction_cutoff
        ]
        for ip in stale_ips:
            del _rate_limit_store[ip]

        timestamps = _rate_limit_store.get(client_ip, [])
        # Prune timestamps outside the sliding window
        timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(timestamps) >= _RATE_LIMIT_MAX_REQUESTS:
            _rate_limit_store[client_ip] = timestamps
            # Retry-After: seconds until the oldest timestamp leaves the window
            retry_after = int(_RATE_LIMIT_WINDOW_SECONDS - (now - timestamps[0])) + 1
            return True, max(retry_after, 1)

        timestamps.append(now)
        _rate_limit_store[client_ip] = timestamps
        return False, 0


def _get_client_ip(raw_request: Request) -> str:
    """Extract the real client IP from the request.

    Falls back to a per-request unique token when the IP cannot be determined
    so that a single unidentifiable client cannot consume the shared 'unknown'
    rate-limit bucket and accidentally throttle other unidentifiable clients.
    """
    if raw_request.client is not None:
        return raw_request.client.host
    # No transport-level peer: assign a unique key so each anonymous request
    # does not share a rate-limit bucket with others.
    return f"anon-{uuid.uuid4()}"


@router.post("/execute", response_model=ExecutionResult)
async def execute(request: ExecutionRequest, raw_request: Request) -> ExecutionResult:
    """Execute user-submitted Python (Cirq) code in a sandbox.

    Rate-limited to 30 requests per minute per client IP.
    Uses asyncio.to_thread to avoid blocking the event loop during
    synchronous subprocess execution.
    """
    client_ip = _get_client_ip(raw_request)
    is_limited, retry_after = _is_rate_limited(client_ip)
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: max {_RATE_LIMIT_MAX_REQUESTS} requests per {_RATE_LIMIT_WINDOW_SECONDS}s",
            headers={"Retry-After": str(retry_after)},
        )
    return await asyncio.to_thread(execute_code, request.code)
