"""Smoke tests for the API."""

from fastapi.testclient import TestClient

from backend.app.server import create_app


def test_health_endpoint_returns_ok() -> None:
    """The /v1/health endpoint should return a healthy status."""

    client = TestClient(create_app())
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"]

