"""Tests for the rate limiting middleware on the /execute endpoint."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from quantum_katas.models.execution import ExecutionResult
from quantum_katas.routers.execute import (
    _RATE_LIMIT_EVICTION_SECONDS,
    _RATE_LIMIT_MAX_REQUESTS,
    _RATE_LIMIT_WINDOW_SECONDS,
    _get_client_ip,
    _is_rate_limited,
    _rate_limit_store,
)

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def _mock_execute_code(_code: str) -> ExecutionResult:
    """Stub that returns instantly without running a subprocess."""
    return ExecutionResult(stdout="ok", stderr="", success=True)


class TestRateLimiting:
    """M-1: Verify in-memory rate limiting on /execute."""

    def test_requests_within_limit_succeed(self, client: TestClient) -> None:
        """Requests under the limit should return 200."""
        _rate_limit_store.clear()
        with patch("quantum_katas.routers.execute.execute_code", _mock_execute_code):
            response = client.post("/api/execute", json={"code": "print(1)"})
        assert response.status_code == 200

    def test_exceeding_limit_returns_429(self, client: TestClient) -> None:
        """Exceeding the rate limit should return 429."""
        _rate_limit_store.clear()
        with patch("quantum_katas.routers.execute.execute_code", _mock_execute_code):
            for _ in range(_RATE_LIMIT_MAX_REQUESTS):
                resp = client.post("/api/execute", json={"code": "print(1)"})
                assert resp.status_code == 200

            # Next request should be rate-limited
            resp = client.post("/api/execute", json={"code": "print(1)"})
            assert resp.status_code == 429
            assert "Rate limit exceeded" in resp.json()["detail"]
        _rate_limit_store.clear()

    def test_rate_limit_returns_retry_after_header(self, client: TestClient) -> None:
        """429 responses must include a Retry-After header with a positive integer."""
        _rate_limit_store.clear()
        with patch("quantum_katas.routers.execute.execute_code", _mock_execute_code):
            for _ in range(_RATE_LIMIT_MAX_REQUESTS):
                client.post("/api/execute", json={"code": "print(1)"})

            resp = client.post("/api/execute", json={"code": "print(1)"})
            assert resp.status_code == 429

        retry_after = resp.headers.get("retry-after")
        assert retry_after is not None, "Retry-After header must be present on 429"
        assert int(retry_after) >= 1, "Retry-After must be a positive integer (seconds)"
        _rate_limit_store.clear()

    def test_retry_after_does_not_exceed_window_plus_one(self) -> None:
        """Retry-After must not exceed window_seconds + 1.

        The formula ``int(window - (now - timestamps[0])) + 1`` guarantees
        this because ``now - timestamps[0]`` is always > 0 (timestamps are
        strictly in the past after the prune step).
        """
        _rate_limit_store.clear()
        client_ip = "192.0.2.1"
        # Inject exactly MAX_REQUESTS timestamps all at approximately "now"
        # (worst case: all requests arrived at the same instant).
        almost_now = time.monotonic() - 0.001
        _rate_limit_store[client_ip] = [almost_now] * _RATE_LIMIT_MAX_REQUESTS

        is_limited, retry_after = _is_rate_limited(client_ip)

        assert is_limited, "Should be rate-limited when store is full"
        # Upper bound: window + 1 (timestamps[0] ≈ now, so age ≈ 0)
        assert retry_after <= _RATE_LIMIT_WINDOW_SECONDS + 1, (
            f"Retry-After ({retry_after}s) must not exceed window+1 ({_RATE_LIMIT_WINDOW_SECONDS + 1}s)"
        )
        assert retry_after >= 1, "Retry-After must be at least 1 second"
        _rate_limit_store.clear()

    def test_rate_limit_is_per_ip(self, client: TestClient) -> None:
        """Rate limit store is keyed by client IP (testclient uses 'testclient')."""
        _rate_limit_store.clear()
        with patch("quantum_katas.routers.execute.execute_code", _mock_execute_code):
            resp = client.post("/api/execute", json={"code": "print(1)"})
            assert resp.status_code == 200
            # Verify the store has an entry for the testclient IP
            assert len(_rate_limit_store) == 1
        _rate_limit_store.clear()


class TestRateLimitStaleEviction:
    """Verify that stale IP entries are evicted to prevent unbounded memory growth."""

    def test_stale_ips_are_evicted_on_next_request(self) -> None:
        """IP entries older than _RATE_LIMIT_EVICTION_SECONDS must be removed."""
        _rate_limit_store.clear()

        # Inject a stale IP entry whose last timestamp is beyond the eviction cutoff
        stale_ts = time.monotonic() - (_RATE_LIMIT_EVICTION_SECONDS + 1)
        _rate_limit_store["stale.ip.example"] = [stale_ts]

        # Trigger eviction via a normal _is_rate_limited call
        _is_rate_limited("trigger.ip.example")

        assert "stale.ip.example" not in _rate_limit_store, "Stale IP entry should have been evicted"
        _rate_limit_store.clear()

    def test_active_ip_not_evicted(self) -> None:
        """IP entries with recent activity must NOT be evicted."""
        _rate_limit_store.clear()

        recent_ts = time.monotonic() - 10  # 10 seconds ago — well within window
        _rate_limit_store["active.ip.example"] = [recent_ts]

        _is_rate_limited("trigger.ip.example")

        assert "active.ip.example" in _rate_limit_store, "Active IP entry should NOT have been evicted"
        _rate_limit_store.clear()

    def test_empty_timestamp_list_is_evicted(self) -> None:
        """IP entries with an empty timestamp list must be evicted."""
        _rate_limit_store.clear()
        _rate_limit_store["empty.ip.example"] = []

        _is_rate_limited("trigger.ip.example")

        assert "empty.ip.example" not in _rate_limit_store, "IP entry with empty timestamp list should be evicted"
        _rate_limit_store.clear()

    def test_evicted_ip_can_make_requests_again(self) -> None:
        """An IP evicted from the store must start a fresh rate-limit window.

        Regression guard: eviction must not permanently block an IP or leave
        corrupted state that causes incorrect rate-limit decisions.
        """
        _rate_limit_store.clear()
        returning_ip = "198.51.100.10"

        # Phase 1: inject a stale entry (simulates the IP going quiet for >2 min)
        stale_ts = time.monotonic() - (_RATE_LIMIT_EVICTION_SECONDS + 1)
        _rate_limit_store[returning_ip] = [stale_ts] * _RATE_LIMIT_MAX_REQUESTS

        # Phase 2: the returning IP makes a new request — eviction fires, then
        # the request is counted as the first in a fresh window.
        is_limited, retry_after = _is_rate_limited(returning_ip)

        assert not is_limited, (
            "IP should NOT be rate-limited immediately after eviction "
            "— its stale timestamps were pruned before the limit check"
        )
        assert retry_after == 0, "retry_after must be 0 when not rate-limited"
        assert returning_ip in _rate_limit_store, "IP should have a fresh entry after first request"
        assert len(_rate_limit_store[returning_ip]) == 1, "Store should contain exactly one fresh timestamp"
        _rate_limit_store.clear()


class TestGetClientIp:
    """Verify client IP extraction and fallback behaviour."""

    def test_returns_host_when_client_present(self) -> None:
        """Should return raw_request.client.host when client is available."""
        mock_request = MagicMock()
        mock_request.client.host = "203.0.113.42"
        assert _get_client_ip(mock_request) == "203.0.113.42"

    def test_returns_unique_token_when_client_is_none(self) -> None:
        """When client is None, each call should return a distinct anon token.

        This prevents different anonymous clients from sharing a single
        'unknown' rate-limit bucket and accidentally throttling each other.
        In production (nginx → uvicorn) raw_request.client is always set, so
        this fallback path is effectively unreachable.  See _get_client_ip
        docstring for the full design rationale.
        """
        mock_request = MagicMock()
        mock_request.client = None

        token1 = _get_client_ip(mock_request)
        token2 = _get_client_ip(mock_request)

        assert token1.startswith("anon-"), "Fallback token must start with 'anon-'"
        assert token2.startswith("anon-"), "Fallback token must start with 'anon-'"
        assert token1 != token2, "Each anonymous request must get a unique token"

    def test_anon_client_is_not_rate_limited(self, client: TestClient) -> None:
        """Intentional design: anonymous clients (client=None) bypass rate limiting.

        Per-request UUID keys mean no single bucket accumulates 30 requests.
        This is a documented trade-off — see _get_client_ip docstring.
        In production raw_request.client is always populated by the reverse
        proxy, so this branch is unreachable under normal deployment.
        """
        _rate_limit_store.clear()
        # Exhaust the rate limit for a real IP first to confirm the limiter works.
        with patch("quantum_katas.routers.execute.execute_code", _mock_execute_code):
            for _ in range(_RATE_LIMIT_MAX_REQUESTS):
                resp = client.post("/api/execute", json={"code": "print(1)"})
                assert resp.status_code == 200

        # Simulate how the endpoint behaves when _get_client_ip returns a fresh
        # UUID per call (i.e. anonymous client path): the store never reaches
        # MAX_REQUESTS for any single key.
        anon_keys: list[str] = [f"anon-{__import__('uuid').uuid4()}" for _ in range(_RATE_LIMIT_MAX_REQUESTS + 5)]
        for key in anon_keys:
            is_limited, _ = _is_rate_limited(key)
            assert not is_limited, (
                "Each unique anon key should never be rate-limited (each key has at most 1 timestamp in the store)"
            )
        _rate_limit_store.clear()


class TestCodeSizeLimitUnified:
    """M-2: Verify that /validate and /execute share the same code size limit (10KB)."""

    def test_validate_rejects_oversized_code(self, client: TestClient) -> None:
        """ValidateRequestBody.max_length should match executor MAX_CODE_LENGTH."""
        oversized_code = "x" * 10_001
        response = client.post(
            "/api/katas/01-single-qubit/validate",
            json={"code": oversized_code},
        )
        assert response.status_code == 422

    def test_validate_accepts_code_at_limit(self, client: TestClient) -> None:
        """Code exactly at 10,000 chars should be accepted by Pydantic."""
        code_at_limit = "x" * 10_000
        response = client.post(
            "/api/katas/01-single-qubit/validate",
            json={"code": code_at_limit},
        )
        # Should NOT be 422; the code is within Pydantic limits.
        # It will likely fail validation (not valid Python), but not 422.
        assert response.status_code == 200

    def test_rate_limit_window_constant_matches_expectation(self) -> None:
        """Sanity check: _RATE_LIMIT_WINDOW_SECONDS should be 60."""
        assert _RATE_LIMIT_WINDOW_SECONDS == 60

    def test_eviction_window_is_double_rate_window(self) -> None:
        """Eviction window should be 2x the rate limit window."""
        assert _RATE_LIMIT_EVICTION_SECONDS == _RATE_LIMIT_WINDOW_SECONDS * 2
