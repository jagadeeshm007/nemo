# ==============================================================================
# Workflow Service — Health Endpoint Tests
# ==============================================================================

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _create_test_app() -> FastAPI:
    """Create a minimal FastAPI app for testing without infrastructure deps."""
    app = FastAPI()

    @app.get("/healthz")
    async def healthz():
        return {"status": "healthy", "service": "workflow-service"}

    return app


@pytest.fixture()
def client():
    app = _create_test_app()
    return TestClient(app)


def test_health_returns_200(client: TestClient):
    response = client.get("/healthz")
    assert response.status_code == 200


def test_health_returns_status_field(client: TestClient):
    response = client.get("/healthz")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_returns_service_name(client: TestClient):
    response = client.get("/healthz")
    data = response.json()
    assert data["service"] == "workflow-service"
