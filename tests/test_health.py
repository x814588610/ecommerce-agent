"""Tests for the health-check endpoint."""
from fastapi.testclient import TestClient

from ecom_agent.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """The health endpoint should report that the service is running."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "development",
    }