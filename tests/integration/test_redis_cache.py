"""Integration tests for Redis cache connectivity."""

from __future__ import annotations

import pytest
import redis

from drishti.config import Settings

pytestmark = pytest.mark.integration


class TestRedisCache:
    def test_set_get_and_delete(self, integration_settings: Settings) -> None:
        client = redis.from_url(integration_settings.redis_url, decode_responses=True)
        key = "drishti:integration:test"
        try:
            assert client.ping() is True
            client.set(key, "ok", ex=60)
            assert client.get(key) == "ok"
        finally:
            client.delete(key)
            client.close()

    def test_incr_and_expire(self, integration_settings: Settings) -> None:
        client = redis.from_url(integration_settings.redis_url, decode_responses=True)
        key = "drishti:integration:counter"
        try:
            client.delete(key)
            assert client.incr(key) == 1
            assert client.incr(key) == 2
            assert client.ttl(key) == -1
            client.expire(key, 30)
            assert client.ttl(key) > 0
        finally:
            client.delete(key)
            client.close()
