"""Tests for the health check endpoint."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_content_type(client: TestClient):
    response = client.get("/health")

    assert response.headers["content-type"] == "application/json"
