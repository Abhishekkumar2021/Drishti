"""Redis-backed Q&A response cache (US-08.03)."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import redis.asyncio as aioredis

if TYPE_CHECKING:
    from drishti.api.schemas import ChatMessage

logger = logging.getLogger(__name__)

_ASK_KEY_PREFIX = "drishti:ask:v1:"


@dataclass(frozen=True)
class CachedAskAnswer:
    """Serialized non-streaming RAG answer for cache replay."""

    question: str
    answer: str
    citations: list[dict[str, object]]
    sources: list[dict[str, object]]


class QueryCache:
    """Caches RAG answers in Redis with TTL and bulk invalidation on ingest."""

    def __init__(
        self,
        redis_url: str,
        *,
        ttl_seconds: int = 3600,
        enabled: bool = True,
    ) -> None:
        """Configure Redis URL, TTL, and whether caching is active."""
        self._redis_url = redis_url
        self._ttl_seconds = max(1, ttl_seconds)
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Return whether ask-response caching is enabled."""
        return self._enabled

    def cache_key(
        self,
        question: str,
        *,
        conversation_history: list[ChatMessage] | None = None,
        filters: dict[str, str] | None = None,
    ) -> str:
        """Compute a stable cache key from query inputs."""
        history_payload = [
            {"role": message.role, "content": message.content}
            for message in (conversation_history or [])
        ]
        payload = {
            "question": question.strip(),
            "history": history_payload,
            "filters": filters or {},
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
        ).hexdigest()
        return f"{_ASK_KEY_PREFIX}{digest}"

    async def get(self, key: str) -> CachedAskAnswer | None:
        """Return a cached answer or None."""
        if not self._enabled:
            return None
        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            raw = await client.get(key)
            if not raw:
                return None
            data = json.loads(raw)
            return CachedAskAnswer(
                question=str(data["question"]),
                answer=str(data["answer"]),
                citations=list(data.get("citations", [])),
                sources=list(data.get("sources", [])),
            )
        except Exception:
            logger.warning("Failed to read ask cache key=%s", key, exc_info=True)
            return None
        finally:
            await client.aclose()

    async def set(self, key: str, answer: CachedAskAnswer) -> None:
        """Store an answer under the cache key."""
        if not self._enabled:
            return
        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            payload = json.dumps(
                {
                    "question": answer.question,
                    "answer": answer.answer,
                    "citations": answer.citations,
                    "sources": answer.sources,
                },
                ensure_ascii=False,
            )
            await client.setex(key, self._ttl_seconds, payload)
        except Exception:
            logger.warning("Failed to write ask cache key=%s", key, exc_info=True)
        finally:
            await client.aclose()

    async def invalidate_all(self) -> int:
        """Delete all cached ask responses (e.g. after repository re-index)."""
        if not self._enabled:
            return 0
        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            deleted = 0
            async for key in client.scan_iter(match=f"{_ASK_KEY_PREFIX}*"):
                await client.delete(key)
                deleted += 1
            return deleted
        except Exception:
            logger.warning("Failed to invalidate ask cache", exc_info=True)
            return 0
        finally:
            await client.aclose()
