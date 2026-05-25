"""FastAPI dependencies for API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from fastapi import Request

from drishti.config import Settings, get_settings
from drishti.services.query_cache import QueryCache
from drishti.services.wiring import create_hybrid_search, create_rag_pipeline

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

    from drishti.agent.runner import AgentRunner
    from drishti.generation.pipeline import RAGPipeline
    from drishti.search.pipeline import HybridSearchPipeline
    from drishti.services.platform_service import PlatformService


def get_app_settings() -> Settings:
    """Dependency that returns application settings."""
    return get_settings()


def get_qdrant_client(request: Request) -> QdrantClient:
    """Return the shared Qdrant client from application state."""
    client = getattr(request.app.state, "qdrant_client", None)
    if client is None:
        msg = "Qdrant client is not initialized"
        raise RuntimeError(msg)
    return cast("QdrantClient", client)


def get_search_pipeline(request: Request) -> HybridSearchPipeline:
    """Return the hybrid search pipeline, creating it on first use."""
    pipeline = getattr(request.app.state, "search_pipeline", None)
    if pipeline is None:
        settings = get_settings()
        client = get_qdrant_client(request)
        pipeline = create_hybrid_search(settings, client=client)
        request.app.state.search_pipeline = pipeline
    return cast("HybridSearchPipeline", pipeline)


def get_rag_pipeline(request: Request) -> RAGPipeline:
    """Return the RAG pipeline, creating it on first use."""
    pipeline = getattr(request.app.state, "rag_pipeline", None)
    if pipeline is None:
        settings = get_settings()
        client = get_qdrant_client(request)
        pipeline = create_rag_pipeline(settings, client=client)
        request.app.state.rag_pipeline = pipeline
    return cast("RAGPipeline", pipeline)


def get_platform_service(request: Request) -> PlatformService:
    """Return the platform service from application state."""
    platform = getattr(request.app.state, "platform_service", None)
    if platform is None:
        msg = "Platform service is not initialized"
        raise RuntimeError(msg)
    return cast("PlatformService", platform)


def get_agent_runner(request: Request) -> AgentRunner:
    """Return the LangGraph agent runner."""
    runner = getattr(request.app.state, "agent_runner", None)
    if runner is None:
        settings = get_settings()
        runner = AgentRunner(get_rag_pipeline(request), settings)
        request.app.state.agent_runner = runner
    return cast("AgentRunner", runner)


def get_query_cache(request: Request) -> QueryCache:
    """Return the query cache from application state."""
    cache = getattr(request.app.state, "query_cache", None)
    if cache is None:
        msg = "Query cache is not initialized"
        raise RuntimeError(msg)
    return cast("QueryCache", cache)
