"""Production platform APIs: workspaces, uploads, conversations, memory."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from starlette.responses import StreamingResponse

from drishti.agent.runner import AgentRunner
from drishti.api.deps import (
    get_agent_runner,
    get_app_settings,
    get_platform_service,
)
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
from drishti.generation.streaming import format_sse_event
from drishti.observability.logging import get_logger
from drishti.services.platform_service import PlatformService
from drishti.services.query_cache import QueryCache
from drishti.services.wiring import create_incremental_indexer
from drishti.utils.workspace_git import ensure_git_snapshot

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Platform"])


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    body: WorkspaceCreateRequest,
    platform: PlatformService = Depends(get_platform_service),
) -> WorkspaceResponse:
    record = await platform.create_workspace(name=body.name, description=body.description)
    return WorkspaceResponse(**record.to_dict())


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    platform: PlatformService = Depends(get_platform_service),
) -> list[WorkspaceResponse]:
    records = await platform.list_workspaces()
    return [WorkspaceResponse(**record.to_dict()) for record in records]


@router.put("/workspaces/{workspace_id}/memory", response_model=WorkspaceMemoryResponse)
async def set_workspace_memory(
    workspace_id: str,
    body: WorkspaceMemoryRequest,
    platform: PlatformService = Depends(get_platform_service),
) -> WorkspaceMemoryResponse:
    if platform.get_workspace(workspace_id) is None:
        raise DrishtiError(f"Unknown workspace: {workspace_id}", code="NOT_FOUND")
    await platform.set_memory(workspace_id, body.memory)
    return WorkspaceMemoryResponse(workspace_id=workspace_id, memory=body.memory)


@router.get("/workspaces/{workspace_id}/memory", response_model=WorkspaceMemoryResponse)
async def get_workspace_memory(
    workspace_id: str,
    platform: PlatformService = Depends(get_platform_service),
) -> WorkspaceMemoryResponse:
    memory = await platform.get_memory(workspace_id)
    return WorkspaceMemoryResponse(workspace_id=workspace_id, memory=memory)


@router.post("/workspaces/{workspace_id}/artifacts", response_model=ArtifactUploadResponse)
async def upload_artifacts(
    workspace_id: str,
    request: Request,
    files: list[UploadFile] = File(...),
    settings: Settings = Depends(get_app_settings),
    platform: PlatformService = Depends(get_platform_service),
) -> ArtifactUploadResponse:
    if platform.get_workspace(workspace_id) is None:
        raise DrishtiError(f"Unknown workspace: {workspace_id}", code="NOT_FOUND")

    saved: list[str] = []
    total_bytes = 0
    for upload in files:
        payload = await upload.read()
        total_bytes += len(payload)
        if total_bytes > settings.max_upload_bytes:
            raise DrishtiError("Upload exceeds max_upload_bytes", code="VALIDATION_ERROR")
        safe_name = Path(upload.filename or "upload.bin").name
        await platform.save_artifact(
            workspace_id,
            safe_name,
            payload,
            content_type=upload.content_type or "application/octet-stream",
        )
        saved.append(safe_name)

    head_commit = await asyncio.to_thread(
        ensure_git_snapshot,
        platform.ingest_root(workspace_id),
        commit_message=f"Upload {len(saved)} artifact(s)",
    )
    await _index_workspace(request, settings, platform, workspace_id, force_full=False)
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
    platform: PlatformService = Depends(get_platform_service),
    force_reindex: bool = Query(default=False),
) -> dict[str, object]:
    if platform.get_workspace(workspace_id) is None:
        raise DrishtiError(f"Unknown workspace: {workspace_id}", code="NOT_FOUND")
    await asyncio.to_thread(
        ensure_git_snapshot,
        platform.ingest_root(workspace_id),
    )
    if settings.worker_enabled:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await pool.enqueue_job(
            "ingest_workspace_task",
            repo_path=str(platform.ingest_root(workspace_id)),
            path_prefix=f"workspaces/{workspace_id}",
            force_full=force_reindex,
        )
        await pool.close()
        return {
            "workspace_id": workspace_id,
            "job_id": job.job_id if job else None,
            "status": "queued",
        }
    result = await _index_workspace(
        request,
        settings,
        platform,
        workspace_id,
        force_full=force_reindex,
    )
    return {"workspace_id": workspace_id, **result}


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    body: ConversationCreateRequest,
    platform: PlatformService = Depends(get_platform_service),
) -> ConversationResponse:
    record = await platform.create_conversation(
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
    platform: PlatformService = Depends(get_platform_service),
) -> ConversationMessagesResponse:
    messages = await platform.get_messages(conversation_id)
    return ConversationMessagesResponse(conversation_id=conversation_id, messages=messages)


@router.post("/conversations/{conversation_id}/ask", response_model=None)
async def ask_in_conversation(
    conversation_id: str,
    body: ConversationAskRequest,
    agent: AgentRunner = Depends(get_agent_runner),
    platform: PlatformService = Depends(get_platform_service),
) -> AskResponse | StreamingResponse:
    record = await platform.get_conversation(conversation_id)
    if record is None:
        raise DrishtiError(f"Unknown conversation: {conversation_id}", code="NOT_FOUND")

    history = await platform.get_messages(conversation_id)
    memory = ""
    filters: dict[str, str] | None = None
    if record.workspace_id:
        memory = await platform.get_memory(record.workspace_id)
        filters = {"file_path": f"workspaces/{record.workspace_id}/*"}

    if body.stream:
        return StreamingResponse(
            _stream_conversation_answer(
                agent,
                platform,
                conversation_id,
                question=body.question,
                history=history,
                filters=filters,
                workspace_memory=memory,
            ),
            media_type="text/event-stream",
        )

    try:
        answer = agent.ask(
            body.question,
            filters=filters,
            conversation_history=history,
            workspace_memory=memory,
        )
    except GenerationError:
        raise
    except Exception as exc:
        raise GenerationError(f"Generation failed: {exc}") from exc

    await platform.append_exchange(
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
    platform: PlatformService,
    workspace_id: str,
    *,
    force_full: bool,
) -> dict[str, object]:
    client = request.app.state.qdrant_client
    indexer = create_incremental_indexer(
        settings,
        platform.ingest_root(workspace_id),
        client=client,
        path_prefix=f"workspaces/{workspace_id}",
    )
    result = await asyncio.to_thread(indexer.run, force_full=force_full)
    cache: QueryCache = request.app.state.query_cache
    await cache.invalidate_all()
    log.info(
        "workspace_indexed",
        workspace_id=workspace_id,
        chunks_indexed=result.chunks_indexed,
        up_to_date=result.up_to_date,
    )
    return {
        "chunks_indexed": result.chunks_indexed,
        "total_chunks_in_store": result.total_chunks_in_store,
        "up_to_date": result.up_to_date,
        "parseable_files": result.parseable_files,
    }


async def _stream_conversation_answer(
    agent: AgentRunner,
    platform: PlatformService,
    conversation_id: str,
    *,
    question: str,
    history: list[ChatMessage],
    filters: dict[str, str] | None,
    workspace_memory: str,
) -> AsyncIterator[str]:
    answer_parts: list[str] = []
    for event in agent.ask_stream(
        question,
        filters=filters,
        conversation_history=history,
        workspace_memory=workspace_memory,
    ):
        if event.event == "token":
            answer_parts.append(str(event.data.get("text", "")))
        yield format_sse_event(event)

    if answer_parts:
        await platform.append_exchange(
            conversation_id,
            user=question,
            assistant="".join(answer_parts),
        )
