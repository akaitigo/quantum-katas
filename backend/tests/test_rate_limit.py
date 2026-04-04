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
        """
        mock_request = MagicMock()
        mock_request.client = None

        token1 = _get_client_ip(mock_request)
        token2 = _get_client_ip(mock_request)

        assert token1.startswith("anon-"), "Fallback token must start with 'anon-'"
        assert token2.startswith("anon-"), "Fallback token must start with 'anon-'"
        assert token1 != token2, "Each anonymous request must get a unique token"


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
