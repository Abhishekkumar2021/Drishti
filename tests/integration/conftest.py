"""Shared fixtures for integration tests (Qdrant + Redis)."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from drishti.config import Settings
from drishti.main import create_app
from drishti.services.health import ServiceStatus, check_qdrant, check_redis

if TYPE_CHECKING:
    from qdrant_client import QdrantClient


def _integration_settings() -> Settings:
    return Settings(
        qdrant_host=os.environ.get("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.environ.get("QDRANT_PORT", "6333")),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        health_check_timeout_seconds=float(os.environ.get("HEALTH_CHECK_TIMEOUT_SECONDS", "5")),
        api_token="",
        debug=True,
    )


async def _wait_for_services(settings: Settings, *, attempts: int = 30, delay: float = 2.0) -> None:
    last_error = "dependencies not ready"
    for attempt in range(1, attempts + 1):
        qdrant_status = await check_qdrant(settings)
        redis_status = await check_redis(settings)
        if qdrant_status == ServiceStatus.CONNECTED and redis_status == ServiceStatus.CONNECTED:
            return
        last_error = f"attempt {attempt}/{attempts}: qdrant={qdrant_status}, redis={redis_status}"
        await asyncio.sleep(delay)
    msg = f"Integration services did not become ready ({last_error})"
    raise RuntimeError(msg)


@pytest.fixture(scope="session")
def integration_settings() -> Settings:
    """Settings pointed at real Qdrant/Redis instances."""
    return _integration_settings()


@pytest.fixture(scope="session", autouse=True)
def ensure_dependencies_ready(integration_settings: Settings) -> None:
    """Fail fast when Docker services are not running."""
    asyncio.run(_wait_for_services(integration_settings))


@pytest.fixture
def live_client(integration_settings: Settings) -> Iterator[TestClient]:
    """FastAPI test client wired to real infrastructure probes."""
    application = create_app(integration_settings)
    with TestClient(application, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture
def qdrant_client(integration_settings: Settings) -> Iterator[QdrantClient]:
    """Qdrant client for storage integration tests."""
    from qdrant_client import QdrantClient

    client = QdrantClient(
        host=integration_settings.qdrant_host,
        port=integration_settings.qdrant_port,
        timeout=integration_settings.health_check_timeout_seconds,
        check_compatibility=False,
    )
    yield client
    client.close()
