"""Server-side conversation persistence (Redis)."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis

from drishti.api.schemas import ChatMessage

logger = logging.getLogger(__name__)

_MAX_MESSAGES = 100


@dataclass(frozen=True)
class ConversationRecord:
    """Stored conversation metadata."""

    id: str
    workspace_id: str | None
    created_at: str
    updated_at: str
    title: str


class ConversationStore:
    """Persist chat histories in Redis for multi-turn RAG."""

    def __init__(
        self,
        redis_url: str,
        *,
        ttl_seconds: int = 86_400 * 7,
        enabled: bool = True,
    ) -> None:
        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._enabled = enabled

    async def create(
        self,
        *,
        workspace_id: str | None = None,
        title: str = "",
    ) -> ConversationRecord:
        conversation_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        record = ConversationRecord(
            id=conversation_id,
            workspace_id=workspace_id,
            created_at=now,
            updated_at=now,
            title=title.strip() or "New conversation",
        )
        if not self._enabled:
            return record

        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            await client.set(
                self._meta_key(conversation_id),
                json.dumps(record.__dict__),
                ex=self._ttl_seconds,
            )
            await client.delete(self._messages_key(conversation_id))
        finally:
            await client.aclose()
        return record

    async def get_record(self, conversation_id: str) -> ConversationRecord | None:
        if not self._enabled:
            return None
        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            meta_raw = await client.get(self._meta_key(conversation_id))
        finally:
            await client.aclose()
        if not meta_raw:
            return None
        payload = json.loads(meta_raw)
        return ConversationRecord(
            id=str(payload["id"]),
            workspace_id=payload.get("workspace_id"),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            title=str(payload.get("title", "")),
        )

    async def get_messages(self, conversation_id: str) -> list[ChatMessage]:
        if not self._enabled:
            return []
        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            raw_items = await client.lrange(self._messages_key(conversation_id), 0, -1)
        finally:
            await client.aclose()
        messages: list[ChatMessage] = []
        for raw in raw_items:
            try:
                payload: dict[str, Any] = json.loads(raw)
                messages.append(ChatMessage.model_validate(payload))
            except (json.JSONDecodeError, ValueError):
                continue
        return messages

    async def append_exchange(
        self,
        conversation_id: str,
        *,
        user: str,
        assistant: str,
    ) -> list[ChatMessage]:
        """Append a user/assistant turn and return the full history."""
        new_messages = [
            ChatMessage(role="user", content=user),
            ChatMessage(role="assistant", content=assistant),
        ]
        if not self._enabled:
            return new_messages

        client = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            key = self._messages_key(conversation_id)
            for message in new_messages:
                await client.rpush(key, message.model_dump_json())
            await client.ltrim(key, -_MAX_MESSAGES, -1)
            await client.expire(key, self._ttl_seconds)
            meta_key = self._meta_key(conversation_id)
            meta_raw = await client.get(meta_key)
            if meta_raw:
                meta = json.loads(meta_raw)
                meta["updated_at"] = datetime.now(UTC).isoformat()
                await client.set(meta_key, json.dumps(meta), ex=self._ttl_seconds)
            raw_items = await client.lrange(key, 0, -1)
        finally:
            await client.aclose()

        history: list[ChatMessage] = []
        for raw in raw_items:
            history.append(ChatMessage.model_validate(json.loads(raw)))
        return history

    @staticmethod
    def _messages_key(conversation_id: str) -> str:
        return f"drishti:conversation:{conversation_id}:messages"

    @staticmethod
    def _meta_key(conversation_id: str) -> str:
        return f"drishti:conversation:{conversation_id}:meta"
