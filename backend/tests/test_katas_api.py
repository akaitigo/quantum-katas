"""Tests for the katas API endpoints."""

import pytest
from fastapi.testclient import TestClient

from quantum_katas.services.kata_registry import reset_cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset kata cache before each test."""
    reset_cache()
    yield
    reset_cache()


class TestListKatas:
    """Tests for GET /api/katas."""

    def test_returns_200(self, client: TestClient):
        response = client.get("/api/katas")
        assert response.status_code == 200

    def test_returns_ten_katas(self, client: TestClient):
        response = client.get("/api/katas")
        data = response.json()
        assert len(data) == 10

    def test_katas_have_summary_fields(self, client: TestClient):
        response = client.get("/api/katas")
        data = response.json()
        for kata in data:
            assert "id" in kata
            assert "title" in kata
            assert "difficulty" in kata
            assert "category" in kata
            assert "prerequisites" in kata

    def test_katas_ordered_by_difficulty(self, client: TestClient):
        response = client.get("/api/katas")
        data = response.json()
        difficulties = [k["difficulty"] for k in data]
        assert difficulties == sorted(difficulties)

    def test_katas_do_not_expose_solution(self, client: TestClient):
        response = client.get("/api/katas")
        data = response.json()
        for kata in data:
            assert "solution_code" not in kata
            assert "template_code" not in kata


class TestGetKata:
    """Tests for GET /api/katas/{kata_id}."""

    def test_returns_200_for_valid_id(self, client: TestClient):
        response = client.get("/api/katas/01-single-qubit")
        assert response.status_code == 200

    def test_returns_kata_detail(self, client: TestClient):
        response = client.get("/api/katas/01-single-qubit")
        data = response.json()
        assert data["id"] == "01-single-qubit"
        assert data["title"] == "量子ビットの基礎"
        assert "template_code" in data
        assert "hints" in data
        assert "description" in data
        assert "explanation" in data

    def test_detail_excludes_solution_code(self, client: TestClient):
        response = client.get("/api/katas/01-single-qubit")
        data = response.json()
        assert "solution_code" not in data

    def test_returns_404_for_invalid_id(self, client: TestClient):
        response = client.get("/api/katas/nonexistent-kata")
        assert response.status_code == 404

    def test_hints_have_three_items(self, client: TestClient):
        response = client.get("/api/katas/01-single-qubit")
        data = response.json()
        assert len(data["hints"]) == 3


class TestValidateKata:
    """Tests for POST /api/katas/{kata_id}/validate."""

    def test_returns_200(self, client: TestClient):
        response = client.post(
            "/api/katas/01-single-qubit/validate",
            json={"code": "print('hello')"},
        )
        assert response.status_code == 200

    @pytest.mark.slow
    def test_correct_solution_passes(self, client: TestClient):
        code = (
            "import cirq\n"
            "q = cirq.LineQubit(0)\n"
            "circuit = cirq.Circuit([cirq.X(q), cirq.measure(q, key='result')])\n"
            "sim = cirq.Simulator()\n"
            "result = sim.run(circuit, repetitions=10)\n"
            "print(result)"
        )
        response = client.post(
            "/api/katas/02-pauli-x-gate/validate",
            json={"code": code},
        )
        data = response.json()
        assert data["passed"] is True

    def test_nonexistent_kata_returns_not_passed(self, client: TestClient):
        response = client.post(
            "/api/katas/nonexistent-kata/validate",
            json={"code": "print('hello')"},
        )
        data = response.json()
        assert data["passed"] is False
        assert "not found" in data["message"].lower()

    def test_empty_code_rejected(self, client: TestClient):
        response = client.post(
            "/api/katas/01-single-qubit/validate",
            json={"code": ""},
        )
        assert response.status_code == 422

    def test_missing_code_rejected(self, client: TestClient):
        response = client.post(
            "/api/katas/01-single-qubit/validate",
            json={},
        )
        assert response.status_code == 422
