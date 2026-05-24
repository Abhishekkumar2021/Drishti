"""Integration tests for HTTP readiness endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


class TestApiReadiness:
    def test_liveness_does_not_require_dependencies(self, live_client: TestClient) -> None:
        response = live_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_readiness_reports_healthy_when_services_up(self, live_client: TestClient) -> None:
        response = live_client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["services"]["qdrant"] == "connected"
        assert body["services"]["redis"] == "connected"

    def test_api_v1_health_alias(self, live_client: TestClient) -> None:
        response = live_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
