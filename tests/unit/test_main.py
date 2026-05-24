"""Unit tests for FastAPI application wiring."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from drishti.config import Settings
from drishti.main import create_app
from drishti.services.health import ServiceStatus

pytestmark = pytest.mark.unit


@pytest.fixture
def client() -> TestClient:
    settings = Settings(api_token="", debug=True)
    services = {
        "qdrant": ServiceStatus.CONNECTED,
        "redis": ServiceStatus.CONNECTED,
        "neo4j": ServiceStatus.DISABLED,
    }
    with patch(
        "drishti.main.probe_dependencies",
        new=AsyncMock(return_value=services),
    ):
        yield TestClient(create_app(settings))


class TestHealthEndpoints:
    def test_liveness_returns_alive(self, client: TestClient) -> None:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_readiness_returns_services(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["services"]["qdrant"] == "connected"

    def test_api_v1_health_alias(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200


class TestAuthentication:
    def test_protected_route_requires_token_when_enabled(self) -> None:
        settings = Settings(api_token="prod-secret", debug=True)
        test_client = TestClient(create_app(settings))
        response = test_client.post(
            "/api/v1/search",
            json={"query": "auth"},
            headers={},
        )
        assert response.status_code == 401

    def test_protected_route_accepts_valid_token(self) -> None:
        settings = Settings(api_token="prod-secret", debug=True)
        test_client = TestClient(create_app(settings))
        response = test_client.post(
            "/api/v1/search",
            json={"query": "auth"},
            headers={"Authorization": "Bearer prod-secret"},
        )
        assert response.status_code != 401
