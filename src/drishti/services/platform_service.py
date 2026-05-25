"""Unified platform service: Postgres + MinIO with filesystem fallback."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from drishti.api.schemas import ChatMessage
from drishti.config import Settings
from drishti.db.models import (
    ArtifactRow,
    ConversationRow,
    MessageRow,
    WorkspaceMemoryRow,
    WorkspaceRow,
)
from drishti.services.conversation_store import ConversationRecord, ConversationStore
from drishti.services.memory_store import WorkspaceMemoryStore
from drishti.services.workspace_store import WorkspaceRecord, WorkspaceStore
from drishti.storage.artifacts import ArtifactStorage

logger = logging.getLogger(__name__)


@dataclass
class PlatformService:
    """Workspace, conversation, memory, and artifact operations."""

    settings: Settings
    workspace_store: WorkspaceStore
    conversation_store: ConversationStore
    memory_store: WorkspaceMemoryStore
    artifact_storage: ArtifactStorage
    session_factory: async_sessionmaker[AsyncSession] | None = None
    _local_memory: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self._local_memory is None:
            self._local_memory = {}

    @classmethod
    def create(cls, settings: Settings) -> PlatformService:
        """Build platform service from settings."""
        root = settings.workspaces_cache_root.strip()
        ws_root = Path(root) if root else Path.home() / ".cache" / "drishti" / "workspaces"
        session_factory = None
        if settings.postgres_enabled:
            from drishti.db.session import create_engine, create_session_factory

            engine = create_engine(
                settings.database_url,
                pool_size=settings.database_pool_size,
            )
            session_factory = create_session_factory(engine)

        artifacts = ArtifactStorage(settings)
        if artifacts.enabled:
            try:
                artifacts.ensure_bucket()
            except Exception:
                logger.warning("MinIO bucket setup skipped (not reachable)", exc_info=True)

        return cls(
            settings=settings,
            workspace_store=WorkspaceStore(ws_root),
            conversation_store=ConversationStore(
                settings.redis_url,
                ttl_seconds=settings.conversation_ttl_seconds,
                enabled=settings.cache_enabled,
            ),
            memory_store=WorkspaceMemoryStore(
                settings.redis_url,
                enabled=settings.cache_enabled,
            ),
            artifact_storage=artifacts,
            session_factory=session_factory,
        )

    def _use_db(self) -> bool:
        return self.session_factory is not None

    async def create_workspace(self, *, name: str, description: str = "") -> WorkspaceRecord:
        """Create workspace on disk and optionally in Postgres."""
        record = self.workspace_store.create(name=name, description=description)
        if not self._use_db():
            return record

        assert self.session_factory is not None
        async with self.session_factory() as session:
            row = WorkspaceRow(
                id=record.id,
                name=record.name,
                description=record.description,
                local_path=str(self.workspace_store.root_path(record.id)),
                sources=list(record.sources),
                created_at=datetime.fromisoformat(record.created_at),
            )
            session.add(row)
            await session.commit()
        return record

    async def list_workspaces(self) -> list[WorkspaceRecord]:
        if not self._use_db():
            return self.workspace_store.list_all()

        assert self.session_factory is not None
        async with self.session_factory() as session:
            result = await session.execute(select(WorkspaceRow).order_by(WorkspaceRow.created_at))
            rows = result.scalars().all()
        return [
            WorkspaceRecord(
                id=row.id,
                name=row.name,
                created_at=row.created_at.isoformat(),
                sources=list(row.sources or []),
                description=row.description or "",
            )
            for row in rows
        ]

    def get_workspace(self, workspace_id: str) -> WorkspaceRecord | None:
        return self.workspace_store.get(workspace_id)

    def ingest_root(self, workspace_id: str) -> Path:
        return self.workspace_store.ingest_root(workspace_id)

    def artifacts_dir(self, workspace_id: str) -> Path:
        return self.workspace_store.artifacts_dir(workspace_id)

    async def set_memory(self, workspace_id: str, memory: str) -> None:
        if self.get_workspace(workspace_id) is None:
            msg = f"Unknown workspace: {workspace_id}"
            raise ValueError(msg)
        if self.memory_store._enabled:
            await self.memory_store.set(workspace_id, memory)
        elif self._local_memory is not None:
            self._local_memory[workspace_id] = memory
        if not self._use_db():
            return

        assert self.session_factory is not None
        async with self.session_factory() as session:
            existing = await session.get(WorkspaceMemoryRow, workspace_id)
            if existing:
                existing.memory = memory
                existing.updated_at = datetime.now(UTC)
            else:
                session.add(WorkspaceMemoryRow(workspace_id=workspace_id, memory=memory))
            await session.commit()

    async def get_memory(self, workspace_id: str) -> str:
        if self._use_db():
            assert self.session_factory is not None
            async with self.session_factory() as session:
                row = await session.get(WorkspaceMemoryRow, workspace_id)
                if row and row.memory.strip():
                    return row.memory
        if self.memory_store._enabled:
            return await self.memory_store.get(workspace_id)
        if self._local_memory is not None:
            return self._local_memory.get(workspace_id, "")
        return ""

    async def save_artifact(
        self,
        workspace_id: str,
        filename: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Persist artifact locally and optionally to MinIO + Postgres."""
        safe_name = Path(filename).name
        local_path = self.artifacts_dir(workspace_id) / safe_name
        local_path.write_bytes(data)

        object_key = ""
        if self.artifact_storage.enabled:
            object_key = self.artifact_storage.put_bytes(
                workspace_id,
                safe_name,
                data,
                content_type=content_type,
            )

        if self._use_db():
            assert self.session_factory is not None
            async with self.session_factory() as session:
                session.add(
                    ArtifactRow(
                        workspace_id=workspace_id,
                        filename=safe_name,
                        object_key=object_key,
                        size_bytes=len(data),
                        content_type=content_type,
                    ),
                )
                await session.commit()
        return safe_name

    async def create_conversation(
        self,
        *,
        workspace_id: str | None = None,
        title: str = "",
    ) -> ConversationRecord:
        if self._use_db():
            return await self._create_conversation_db(workspace_id=workspace_id, title=title)
        return await self.conversation_store.create(workspace_id=workspace_id, title=title)

    async def _create_conversation_db(
        self,
        *,
        workspace_id: str | None,
        title: str,
    ) -> ConversationRecord:
        assert self.session_factory is not None
        conv_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            session.add(
                ConversationRow(
                    id=conv_id,
                    workspace_id=workspace_id,
                    title=title.strip() or "New conversation",
                    created_at=now,
                    updated_at=now,
                ),
            )
            await session.commit()
        return ConversationRecord(
            id=conv_id,
            workspace_id=workspace_id,
            title=title.strip() or "New conversation",
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )

    async def get_conversation(self, conversation_id: str) -> ConversationRecord | None:
        if not self._use_db():
            return await self.conversation_store.get_record(conversation_id)

        assert self.session_factory is not None
        async with self.session_factory() as session:
            row = await session.get(ConversationRow, conversation_id)
            if row is None:
                return None
            return ConversationRecord(
                id=row.id,
                workspace_id=row.workspace_id,
                title=row.title,
                created_at=row.created_at.isoformat(),
                updated_at=row.updated_at.isoformat(),
            )

    async def get_messages(self, conversation_id: str) -> list[ChatMessage]:
        if not self._use_db():
            return await self.conversation_store.get_messages(conversation_id)

        assert self.session_factory is not None
        async with self.session_factory() as session:
            result = await session.execute(
                select(MessageRow)
                .where(MessageRow.conversation_id == conversation_id)
                .order_by(MessageRow.created_at),
            )
            rows = result.scalars().all()
        return [
            ChatMessage(role=row.role, content=row.content)  # type: ignore[arg-type]
            for row in rows
        ]

    async def append_exchange(
        self,
        conversation_id: str,
        *,
        user: str,
        assistant: str,
    ) -> None:
        if not self._use_db():
            await self.conversation_store.append_exchange(
                conversation_id,
                user=user,
                assistant=assistant,
            )
            return

        assert self.session_factory is not None
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            session.add_all(
                [
                    MessageRow(
                        conversation_id=conversation_id,
                        role="user",
                        content=user,
                        created_at=now,
                    ),
                    MessageRow(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=assistant,
                        created_at=now,
                    ),
                ],
            )
            await session.execute(
                update(ConversationRow)
                .where(ConversationRow.id == conversation_id)
                .values(updated_at=now),
            )
            await session.commit()
