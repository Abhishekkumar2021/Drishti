"""Unit tests for Redis query cache."""

from __future__ import annotations

import pytest

from drishti.api.schemas import ChatMessage
from drishti.services.query_cache import CachedAskAnswer, QueryCache

pytestmark = pytest.mark.unit


class TestQueryCache:
    def test_cache_key_is_stable(self) -> None:
        cache = QueryCache("redis://localhost:6379/0", enabled=False)
        key_a = cache.cache_key(
            "What is auth?",
            conversation_history=[ChatMessage(role="user", content="hi")],
            filters={"language": "python"},
        )
        key_b = cache.cache_key(
            "What is auth?",
            conversation_history=[ChatMessage(role="user", content="hi")],
            filters={"language": "python"},
        )
        assert key_a == key_b
        assert key_a.startswith("drishti:ask:v1:")

    def test_cache_key_changes_with_question(self) -> None:
        cache = QueryCache("redis://localhost:6379/0", enabled=False)
        assert cache.cache_key("a") != cache.cache_key("b")

    @pytest.mark.asyncio
    async def test_disabled_cache_returns_none(self) -> None:
        cache = QueryCache("redis://localhost:6379/0", enabled=False)
        assert await cache.get("drishti:ask:v1:abc") is None
        await cache.set(
            "drishti:ask:v1:abc",
            CachedAskAnswer(question="q", answer="a", citations=[], sources=[]),
        )
        assert await cache.get("drishti:ask:v1:abc") is None
