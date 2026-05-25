"""Workspace-scoped long-term memory for agent context (Redis)."""

from __future__ import annotations

import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class WorkspaceMemoryStore:
    """Store durable notes the agent should remember across conversations."""

    def __init__(
        self,
        redis_url: str,
        *,
        ttl_seconds: int = 86_400 * 30,
        enabled: bool = True,
    ) -> None:
        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._enabled = enabled

    async def get(self, workspace_id: str) -> str:
        if not self._enabled or not workspace_id.strip():
            return ""
        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            value = await client.get(self._key(workspace_id))
        finally:
            await client.aclose()
        return value or ""

    async def set(self, workspace_id: str, memory: str) -> None:
        if not self._enabled or not workspace_id.strip():
            return
        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            key = self._key(workspace_id)
            if memory.strip():
                await client.set(key, memory.strip(), ex=self._ttl_seconds)
            else:
                await client.delete(key)
        finally:
            await client.aclose()

    @staticmethod
    def _key(workspace_id: str) -> str:
        return f"drishti:workspace:{workspace_id}:memory"
