"""Dependency health probes for readiness checks."""

from __future__ import annotations

import logging
from enum import StrEnum

import httpx
import redis.asyncio as aioredis

from drishti.config import Settings

logger = logging.getLogger(__name__)


class ServiceStatus(StrEnum):
    """Connectivity status for an infrastructure dependency."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"


async def check_qdrant(settings: Settings) -> ServiceStatus:
    """Ping the Qdrant HTTP health endpoint."""
    url = f"{settings.qdrant_url.rstrip('/')}/healthz"
    try:
        async with httpx.AsyncClient(timeout=settings.health_check_timeout_seconds) as client:
            response = await client.get(url)
            response.raise_for_status()
        return ServiceStatus.CONNECTED
    except Exception:
        logger.warning("Qdrant health check failed for %s", url, exc_info=True)
        return ServiceStatus.DISCONNECTED


async def check_redis(settings: Settings) -> ServiceStatus:
    """Ping the configured Redis instance."""
    client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        pong = await client.ping()  # type: ignore[misc]
        if pong:
            return ServiceStatus.CONNECTED
        return ServiceStatus.DISCONNECTED
    except Exception:
        logger.warning("Redis health check failed for %s", settings.redis_url, exc_info=True)
        return ServiceStatus.DISCONNECTED
    finally:
        await client.aclose()


async def check_neo4j(settings: Settings) -> ServiceStatus:
    """Report Neo4j status (graph features are optional until EPIC-09)."""
    if not settings.neo4j_enabled:
        return ServiceStatus.DISABLED
    if not settings.neo4j_password:
        return ServiceStatus.NOT_CONFIGURED
    return ServiceStatus.NOT_CONFIGURED


async def check_embedding(settings: Settings) -> ServiceStatus:
    """Verify the configured embedding provider is reachable."""
    if settings.embedding_provider == "hashing":
        return ServiceStatus.CONNECTED

    if settings.embedding_provider == "ollama":
        base = settings.resolved_embedding_api_base().rstrip("/")
        url = f"{base}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=settings.health_check_timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
            return ServiceStatus.CONNECTED
        except Exception:
            logger.warning("Ollama embedding health check failed for %s", url, exc_info=True)
            return ServiceStatus.DISCONNECTED

    return ServiceStatus.CONNECTED


async def probe_dependencies(settings: Settings) -> dict[str, ServiceStatus]:
    """Run all infrastructure health probes."""
    return {
        "qdrant": await check_qdrant(settings),
        "redis": await check_redis(settings),
        "neo4j": await check_neo4j(settings),
        "embedding": await check_embedding(settings),
    }
