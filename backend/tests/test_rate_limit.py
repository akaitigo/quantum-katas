"""Tests for the rate limiting middleware on the /execute endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from quantum_katas.models.execution import ExecutionResult
from quantum_katas.routers.execute import (
    _RATE_LIMIT_MAX_REQUESTS,
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

    def test_rate_limit_is_per_ip(self, client: TestClient) -> None:
        """Rate limit store is keyed by client IP (testclient uses 'testclient')."""
        _rate_limit_store.clear()
        with patch("quantum_katas.routers.execute.execute_code", _mock_execute_code):
            resp = client.post("/api/execute", json={"code": "print(1)"})
            assert resp.status_code == 200
            # Verify the store has an entry for the testclient IP
            assert len(_rate_limit_store) == 1
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
