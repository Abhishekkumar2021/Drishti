"""Integration tests for infrastructure health probes."""

from __future__ import annotations

import pytest

from drishti.config import Settings
from drishti.services.health import ServiceStatus, check_qdrant, check_redis, probe_dependencies

pytestmark = pytest.mark.integration


class TestHealthProbes:
    @pytest.mark.asyncio
    async def test_qdrant_is_connected(self, integration_settings: Settings) -> None:
        assert await check_qdrant(integration_settings) == ServiceStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_redis_is_connected(self, integration_settings: Settings) -> None:
        assert await check_redis(integration_settings) == ServiceStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_probe_dependencies_reports_critical_services(
        self,
        integration_settings: Settings,
    ) -> None:
        services = await probe_dependencies(integration_settings)
        assert services["qdrant"] == ServiceStatus.CONNECTED
        assert services["redis"] == ServiceStatus.CONNECTED
        assert services["neo4j"] == ServiceStatus.DISABLED
