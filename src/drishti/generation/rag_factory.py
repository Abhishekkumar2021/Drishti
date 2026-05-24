"""Factory to wire the full RAG pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drishti.embedding.dense import HashingDenseEmbedder
from drishti.generation.context import ContextBuilder
from drishti.generation.factory import create_chat_llm
from drishti.generation.pipeline import RAGPipeline
from drishti.search.factory import build_hybrid_search_pipeline

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

    from drishti.config import Settings
    from drishti.embedding.dense import DenseEmbedder


def build_rag_pipeline(
    settings: Settings,
    *,
    client: QdrantClient,
    dense_embedder: DenseEmbedder | None = None,
) -> RAGPipeline:
    """Construct a RAG pipeline with hybrid search and configured LLM."""
    embedder = dense_embedder or _default_embedder(settings)
    search = build_hybrid_search_pipeline(settings, client=client, dense_embedder=embedder)
    return RAGPipeline(
        search=search,
        llm=create_chat_llm(settings),
        context_builder=ContextBuilder(
            max_chars=settings.rag_max_context_chars,
            max_chunks=settings.max_context_chunks,
        ),
        settings=settings,
    )


def _default_embedder(settings: Settings) -> DenseEmbedder:
    if settings.openai_api_key.strip():
        from drishti.embedding.dense import OpenAIDenseEmbeddingClient

        return OpenAIDenseEmbeddingClient(settings)
    return HashingDenseEmbedder(dimensions=settings.openai_embedding_dimensions)
