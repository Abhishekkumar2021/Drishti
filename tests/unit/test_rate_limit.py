"""Unit tests for rate limiting middleware."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from drishti.config import Settings
from drishti.middleware.rate_limit import RateLimitMiddleware

pytestmark = pytest.mark.unit


def _build_app(*, enabled: bool = True, limit: int = 2) -> FastAPI:
    settings = Settings(rate_limit_enabled=enabled, rate_limit_requests_per_minute=limit)
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, settings=settings)

    @app.get("/api/v1/search")
    async def search() -> dict[str, str]:
        return {"ok": "true"}

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    return app


class TestRateLimitMiddleware:
    def test_exempt_health_path(self) -> None:
        client = TestClient(_build_app())
        for _ in range(5):
            assert client.get("/api/v1/health").status_code == 200

    def test_returns_429_when_limit_exceeded(self) -> None:
        mock_client = MagicMock()
        mock_client.incr = AsyncMock(side_effect=[1, 2, 3])
        mock_client.expire = AsyncMock()
        mock_client.aclose = AsyncMock()

        with patch(
            "drishti.middleware.rate_limit.aioredis.from_url",
            return_value=mock_client,
        ):
            client = TestClient(_build_app(limit=2))
            assert client.get("/api/v1/search").status_code == 200
            assert client.get("/api/v1/search").status_code == 200
            response = client.get("/api/v1/search")
            assert response.status_code == 429
            assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_disabled_middleware_allows_all(self) -> None:
        client = TestClient(_build_app(enabled=False))
        for _ in range(5):
            assert client.get("/api/v1/search").status_code == 200
