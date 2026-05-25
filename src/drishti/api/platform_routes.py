"""Production platform APIs: workspaces, uploads, conversations, memory."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from starlette.responses import StreamingResponse

from drishti.api.deps import get_app_settings, get_query_cache, get_rag_pipeline
from drishti.api.mappers import citation_to_item, rag_answer_to_sources
from drishti.api.platform_schemas import (
    ArtifactUploadResponse,
    ConversationAskRequest,
    ConversationCreateRequest,
    ConversationMessagesResponse,
    ConversationResponse,
    WorkspaceCreateRequest,
    WorkspaceMemoryRequest,
    WorkspaceMemoryResponse,
    WorkspaceResponse,
)
from drishti.api.responses import AskResponse
from drishti.api.schemas import ChatMessage
from drishti.config import Settings
from drishti.exceptions import DrishtiError, GenerationError
from drishti.generation.pipeline import RAGPipeline
from drishti.generation.streaming import format_sse_event
from drishti.services.conversation_store import ConversationStore
from drishti.services.memory_store import WorkspaceMemoryStore
from drishti.services.query_cache import QueryCache
from drishti.services.wiring import create_incremental_indexer
from drishti.services.workspace_store import WorkspaceStore
from drishti.utils.workspace_git import ensure_git_snapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Platform"])


def _workspace_store(settings: Settings) -> WorkspaceStore:
    root = settings.workspaces_cache_root.strip()
    if root:
        return WorkspaceStore(Path(root))
    return WorkspaceStore.default()


def _conversation_store(settings: Settings) -> ConversationStore:
    return ConversationStore(
        settings.redis_url,
        ttl_seconds=settings.conversation_ttl_seconds,
        enabled=settings.cache_enabled,
    )


def _memory_store(settings: Settings) -> WorkspaceMemoryStore:
    return WorkspaceMemoryStore(settings.redis_url, enabled=settings.cache_enabled)


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    body: WorkspaceCreateRequest,
    settings: Settings = Depends(get_app_settings),
) -> WorkspaceResponse:
    record = _workspace_store(settings).create(name=body.name, description=body.description)
    return WorkspaceResponse(**record.to_dict())


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    settings: Settings = Depends(get_app_settings),
) -> list[WorkspaceResponse]:
    return [WorkspaceResponse(**record.to_dict()) for record in _workspace_store(settings).list_all()]


@router.put("/workspaces/{workspace_id}/memory", response_model=WorkspaceMemoryResponse)
async def set_workspace_memory(
    workspace_id: str,
    body: WorkspaceMemoryRequest,
    settings: Settings = Depends(get_app_settings),
) -> WorkspaceMemoryResponse:
    if _workspace_store(settings).get(workspace_id) is None:
        raise DrishtiError(f"Unknown workspace: {workspace_id}", code="NOT_FOUND")
    await _memory_store(settings).set(workspace_id, body.memory)
    return WorkspaceMemoryResponse(workspace_id=workspace_id, memory=body.memory)


@router.get("/workspaces/{workspace_id}/memory", response_model=WorkspaceMemoryResponse)
async def get_workspace_memory(
    workspace_id: str,
    settings: Settings = Depends(get_app_settings),
) -> WorkspaceMemoryResponse:
    memory = await _memory_store(settings).get(workspace_id)
    return WorkspaceMemoryResponse(workspace_id=workspace_id, memory=memory)


@router.post("/workspaces/{workspace_id}/artifacts", response_model=ArtifactUploadResponse)
async def upload_artifacts(
    workspace_id: str,
    request: Request,
    files: list[UploadFile] = File(...),
    settings: Settings = Depends(get_app_settings),
) -> ArtifactUploadResponse:
    ws_store = _workspace_store(settings)
    if ws_store.get(workspace_id) is None:
        raise DrishtiError(f"Unknown workspace: {workspace_id}", code="NOT_FOUND")

    artifacts_dir = ws_store.artifacts_dir(workspace_id)
    saved: list[str] = []
    total_bytes = 0
    for upload in files:
        payload = await upload.read()
        total_bytes += len(payload)
        if total_bytes > settings.max_upload_bytes:
            raise DrishtiError("Upload exceeds max_upload_bytes", code="VALIDATION_ERROR")
        safe_name = Path(upload.filename or "upload.bin").name
        (artifacts_dir / safe_name).write_bytes(payload)
        saved.append(safe_name)

    head_commit = await asyncio.to_thread(
        ensure_git_snapshot,
        ws_store.ingest_root(workspace_id),
        commit_message=f"Upload {len(saved)} artifact(s)",
    )
    await _index_workspace(request, settings, workspace_id, force_full=False)
    return ArtifactUploadResponse(
        workspace_id=workspace_id,
        saved_files=saved,
        head_commit=head_commit,
    )


@router.post("/workspaces/{workspace_id}/ingest")
async def ingest_workspace(
    workspace_id: str,
    request: Request,
    settings: Settings = Depends(get_app_settings),
    force_reindex: bool = Query(default=False),
) -> dict[str, object]:
    if _workspace_store(settings).get(workspace_id) is None:
        raise DrishtiError(f"Unknown workspace: {workspace_id}", code="NOT_FOUND")
    await asyncio.to_thread(
        ensure_git_snapshot,
        _workspace_store(settings).ingest_root(workspace_id),
    )
    result = await _index_workspace(request, settings, workspace_id, force_full=force_reindex)
    return {"workspace_id": workspace_id, **result}


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    body: ConversationCreateRequest,
    settings: Settings = Depends(get_app_settings),
) -> ConversationResponse:
    record = await _conversation_store(settings).create(
        workspace_id=body.workspace_id,
        title=body.title,
    )
    return ConversationResponse(
        id=record.id,
        workspace_id=record.workspace_id,
        title=record.title,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
)
async def get_conversation_messages(
    conversation_id: str,
    settings: Settings = Depends(get_app_settings),
) -> ConversationMessagesResponse:
    messages = await _conversation_store(settings).get_messages(conversation_id)
    return ConversationMessagesResponse(conversation_id=conversation_id, messages=messages)


@router.post("/conversations/{conversation_id}/ask", response_model=None)
async def ask_in_conversation(
    conversation_id: str,
    body: ConversationAskRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline),
    settings: Settings = Depends(get_app_settings),
):
    conv_store = _conversation_store(settings)
    record = await conv_store.get_record(conversation_id)
    if record is None:
        raise DrishtiError(f"Unknown conversation: {conversation_id}", code="NOT_FOUND")

    history = await conv_store.get_messages(conversation_id)
    memory = ""
    filters: dict[str, str] | None = None
    if record.workspace_id:
        memory = await _memory_store(settings).get(record.workspace_id)
        filters = {"file_path": f"workspaces/{record.workspace_id}/*"}

    if body.stream:
        return StreamingResponse(
            _stream_conversation_answer(
                rag,
                conv_store,
                conversation_id,
                question=body.question,
                history=history,
                filters=filters,
                workspace_memory=memory,
            ),
            media_type="text/event-stream",
        )

    try:
        answer = rag.ask(
            body.question,
            filters=filters,
            conversation_history=history,
            workspace_memory=memory,
        )
    except GenerationError:
        raise
    except Exception as exc:
        raise GenerationError(f"Generation failed: {exc}") from exc

    await conv_store.append_exchange(
        conversation_id,
        user=body.question,
        assistant=answer.answer,
    )
    return AskResponse(
        question=answer.question,
        answer=answer.answer,
        citations=[citation_to_item(citation) for citation in answer.citations],
        sources=rag_answer_to_sources(answer),
        cached=False,
    )


async def _index_workspace(
    request: Request,
    settings: Settings,
    workspace_id: str,
    *,
    force_full: bool,
) -> dict[str, object]:
    ws_store = _workspace_store(settings)
    client = request.app.state.qdrant_client
    indexer = create_incremental_indexer(
        settings,
        ws_store.ingest_root(workspace_id),
        client=client,
        path_prefix=f"workspaces/{workspace_id}",
    )
    result = await asyncio.to_thread(indexer.run, force_full=force_full)
    cache: QueryCache = request.app.state.query_cache
    await cache.invalidate_all()
    return {
        "chunks_indexed": result.chunks_indexed,
        "total_chunks_in_store": result.total_chunks_in_store,
        "up_to_date": result.up_to_date,
        "parseable_files": result.parseable_files,
    }


async def _stream_conversation_answer(
    rag: RAGPipeline,
    conv_store: ConversationStore,
    conversation_id: str,
    *,
    question: str,
    history: list[ChatMessage],
    filters: dict[str, str] | None,
    workspace_memory: str,
) -> AsyncIterator[str]:
    answer_parts: list[str] = []
    for event in rag.ask_stream(
        question,
        filters=filters,
        conversation_history=history,
        workspace_memory=workspace_memory,
    ):
        if event.event == "token":
            answer_parts.append(str(event.data.get("text", "")))
        yield format_sse_event(event)

    if answer_parts:
        await conv_store.append_exchange(
            conversation_id,
            user=question,
            assistant="".join(answer_parts),
        )
