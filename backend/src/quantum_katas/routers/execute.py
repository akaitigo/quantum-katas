"""Code execution router with in-memory rate limiting."""

from __future__ import annotations

import asyncio
import threading
import time

from fastapi import APIRouter, HTTPException, Request

from quantum_katas.models.execution import ExecutionRequest, ExecutionResult
from quantum_katas.services.executor import execute_code

router = APIRouter()

# ---------------------------------------------------------------------------
# M-1: Simple in-memory sliding-window rate limiter (30 requests/minute/IP)
# ---------------------------------------------------------------------------
_RATE_LIMIT_WINDOW_SECONDS: int = 60
_RATE_LIMIT_MAX_REQUESTS: int = 30

_rate_limit_store: dict[str, list[float]] = {}
_rate_limit_lock = threading.Lock()


def _is_rate_limited(client_ip: str) -> bool:
    """Return True if *client_ip* has exceeded the rate limit."""
    now = time.monotonic()
    cutoff = now - _RATE_LIMIT_WINDOW_SECONDS

    with _rate_limit_lock:
        timestamps = _rate_limit_store.get(client_ip, [])
        # Prune expired entries
        timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(timestamps) >= _RATE_LIMIT_MAX_REQUESTS:
            _rate_limit_store[client_ip] = timestamps
            return True

        timestamps.append(now)
        _rate_limit_store[client_ip] = timestamps
        return False


@router.post("/execute", response_model=ExecutionResult)
async def execute(request: ExecutionRequest, raw_request: Request) -> ExecutionResult:
    """Execute user-submitted Python (Cirq) code in a sandbox.

    Rate-limited to 30 requests per minute per client IP.
    Uses asyncio.to_thread to avoid blocking the event loop during
    synchronous subprocess execution.
    """
    client_ip = raw_request.client.host if raw_request.client else "unknown"
    if _is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: max {_RATE_LIMIT_MAX_REQUESTS} requests per {_RATE_LIMIT_WINDOW_SECONDS}s",
        )
    return await asyncio.to_thread(execute_code, request.code)
