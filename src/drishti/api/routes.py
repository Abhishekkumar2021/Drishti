"""REST API routes for ingest, search, and ask (EPIC-08)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from starlette.requests import Request

from drishti.api.deps import (
    get_app_settings,
    get_query_cache,
    get_rag_pipeline,
    get_search_pipeline,
)
from drishti.api.mappers import (
    citation_to_item,
    rag_answer_to_sources,
    search_hit_to_item,
)
from drishti.api.responses import (
    AskResponse,
    CitationItem,
    IngestResponse,
    SearchResponse,
    SearchResultItem,
)
from drishti.api.schemas import AskRequest, ChatMessage, IngestionRequest, SearchRequest
from drishti.config import Settings
from drishti.exceptions import (
    DrishtiError,
    GenerationError,
    GitRepositoryError,
    PathValidationError,
    SearchError,
)
from drishti.generation.models import Citation, StreamEvent
from drishti.generation.pipeline import RAGPipeline
from drishti.generation.streaming import citation_event, done_event, format_sse_event, token_event
from drishti.search.pipeline import HybridSearchPipeline
from drishti.services.query_cache import CachedAskAnswer, QueryCache
from drishti.services.wiring import create_incremental_indexer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["API"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_repository(
    body: IngestionRequest,
    request: Request,
    settings: Settings = Depends(get_app_settings),
) -> IngestResponse:
    """Trigger incremental indexing for a git repository."""
    allowed_roots = [Path(root) for root in settings.ingestion_root_allowlist()]
    try:
        repo_path = body.resolved_repo_path(allowed_roots=allowed_roots or None)
    except ValueError as exc:
        raise PathValidationError(str(exc)) from exc

    client = request.app.state.qdrant_client
    indexer = create_incremental_indexer(settings, repo_path, client=client)

    try:
        result = await asyncio.to_thread(
            indexer.run,
            force_full=body.force_reindex,
        )
    except GitRepositoryError:
        raise
    except Exception as exc:
        msg = f"Ingestion failed: {exc}"
        raise DrishtiError(msg, code="INGESTION_ERROR") from exc

    cache: QueryCache = request.app.state.query_cache
    await cache.invalidate_all()

    return IngestResponse(
        head_commit=result.head_commit,
        base_commit=result.base_commit,
        added=list(result.added),
        modified=list(result.modified),
        deleted=list(result.deleted),
        chunks_indexed=result.chunks_indexed,
        chunks_removed=result.chunks_removed,
        files_parsed=result.files_parsed,
    )


@router.post("/search", response_model=SearchResponse)
async def search_chunks(
    body: SearchRequest,
    search: HybridSearchPipeline = Depends(get_search_pipeline),
) -> SearchResponse:
    """Run hybrid dense+sparse search with optional metadata filters."""
    try:
        hits = search.search(body.query, filters=body.filters, limit=body.limit)
    except Exception as exc:
        msg = f"Search failed: {exc}"
        raise SearchError(msg) from exc

    return SearchResponse(
        query=body.query,
        results=[search_hit_to_item(hit) for hit in hits],
    )


@router.post("/ask", response_model=None)
async def ask_question(
    body: AskRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline),
    cache: QueryCache = Depends(get_query_cache),
    stream: bool = Query(default=True, description="Stream answer via SSE when true"),
) -> AskResponse | StreamingResponse:
    """Answer a question using RAG; streams tokens via SSE by default."""
    cache_key = cache.cache_key(
        body.question,
        conversation_history=body.conversation_history,
        filters=body.filters,
    )

    if cache.enabled:
        cached = await cache.get(cache_key)
        if cached is not None:
            if stream:
                return StreamingResponse(
                    _stream_cached_answer(cached),
                    media_type="text/event-stream",
                )
            return _ask_response_from_cache(cached)

    if stream:
        return StreamingResponse(
            _stream_rag_with_cache(
                rag,
                cache,
                cache_key,
                question=body.question,
                filters=body.filters,
                conversation_history=body.conversation_history,
            ),
            media_type="text/event-stream",
        )

    try:
        answer = rag.ask(
            body.question,
            filters=body.filters,
            conversation_history=body.conversation_history,
        )
    except GenerationError:
        raise
    except Exception as exc:
        msg = f"Generation failed: {exc}"
        raise GenerationError(msg) from exc

    response = AskResponse(
        question=answer.question,
        answer=answer.answer,
        citations=[citation_to_item(citation) for citation in answer.citations],
        sources=rag_answer_to_sources(answer),
        cached=False,
    )
    await _store_cache(cache, cache_key, response)
    return response


def _ask_response_from_cache(cached: CachedAskAnswer) -> AskResponse:
    return AskResponse(
        question=cached.question,
        answer=cached.answer,
        citations=[CitationItem.model_validate(item) for item in cached.citations],
        sources=[SearchResultItem.model_validate(item) for item in cached.sources],
        cached=True,
    )


async def _stream_cached_answer(cached: CachedAskAnswer) -> AsyncIterator[str]:
    yield format_sse_event(StreamEvent(event="context", data={"sources": cached.sources}))
    yield format_sse_event(token_event(cached.answer))
    for item in cached.citations:
        start_line = item.get("start_line")
        end_line = item.get("end_line")
        citation = Citation(
            citation_tag=str(item.get("citation_tag", "")),
            file_path=str(item.get("file_path", "")),
            start_line=int(start_line) if isinstance(start_line, int) else None,
            end_line=int(end_line) if isinstance(end_line, int) else None,
            valid=bool(item.get("valid", True)),
        )
        yield format_sse_event(citation_event(citation))
    yield format_sse_event(done_event(total_tokens=len(cached.answer.split()), execution_time_ms=0))


async def _stream_rag_with_cache(
    rag: RAGPipeline,
    cache: QueryCache,
    cache_key: str,
    *,
    question: str,
    filters: dict[str, str] | None,
    conversation_history: list[ChatMessage],
) -> AsyncIterator[str]:
    answer_parts: list[str] = []
    citations: list[CitationItem] = []
    sources: list[dict[str, object]] = []

    for event in rag.ask_stream(
        question,
        filters=filters,
        conversation_history=conversation_history,
    ):
        if event.event == "token":
            answer_parts.append(str(event.data.get("text", "")))
        elif event.event == "context":
            sources = list(event.data.get("sources", []))
        elif event.event == "citation":
            citations.append(CitationItem.model_validate(event.data))
        yield format_sse_event(event)

    await cache.set(
        cache_key,
        CachedAskAnswer(
            question=question.strip(),
            answer="".join(answer_parts),
            citations=[item.model_dump() for item in citations],
            sources=sources,
        ),
    )


async def _store_cache(cache: QueryCache, key: str, response: AskResponse) -> None:
    await cache.set(
        key,
        CachedAskAnswer(
            question=response.question,
            answer=response.answer,
            citations=[item.model_dump() for item in response.citations],
            sources=[item.model_dump() for item in response.sources],
        ),
    )
