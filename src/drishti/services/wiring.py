"""Factory helpers for API-layer dependency wiring."""

from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient

from drishti.config import Settings
from drishti.embedding.dense import DenseEmbedder, HashingDenseEmbedder, OpenAIDenseEmbeddingClient
from drishti.embedding.pipeline import ChunkEmbeddingPipeline
from drishti.embedding.sparse import BM25SparseEncoder
from drishti.generation.pipeline import RAGPipeline
from drishti.generation.rag_factory import build_rag_pipeline
from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.incremental import IncrementalIndexer
from drishti.search.factory import build_hybrid_search_pipeline
from drishti.search.pipeline import HybridSearchPipeline
from drishti.storage.qdrant_store import QdrantChunkStore


def create_dense_embedder(settings: Settings) -> DenseEmbedder:
    """Return the configured dense embedder or a deterministic fallback."""
    if settings.openai_api_key.strip():
        return OpenAIDenseEmbeddingClient(settings)
    return HashingDenseEmbedder(dimensions=settings.openai_embedding_dimensions)


def create_qdrant_client(settings: Settings) -> QdrantClient:
    """Construct a Qdrant client from application settings."""
    timeout_seconds = int(settings.health_check_timeout_seconds)
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        timeout=timeout_seconds,
        check_compatibility=False,
    )


def create_chunk_store(
    settings: Settings,
    *,
    client: QdrantClient | None = None,
) -> QdrantChunkStore:
    """Build a Qdrant-backed chunk index with embedding pipeline."""
    embedder = create_dense_embedder(settings)
    pipeline = ChunkEmbeddingPipeline(embedder, sparse_encoder=BM25SparseEncoder())
    return QdrantChunkStore(settings, pipeline, client=client)


def create_hybrid_search(
    settings: Settings,
    *,
    client: QdrantClient | None = None,
) -> HybridSearchPipeline:
    """Build the hybrid search pipeline."""
    qdrant = client or create_qdrant_client(settings)
    embedder = create_dense_embedder(settings)
    return build_hybrid_search_pipeline(settings, client=qdrant, dense_embedder=embedder)


def create_rag_pipeline(
    settings: Settings,
    *,
    client: QdrantClient | None = None,
) -> RAGPipeline:
    """Build the full RAG pipeline."""
    qdrant = client or create_qdrant_client(settings)
    return build_rag_pipeline(settings, client=qdrant)


def create_incremental_indexer(
    settings: Settings,
    repo_root: Path,
    *,
    client: QdrantClient | None = None,
) -> IncrementalIndexer:
    """Wire an incremental indexer for a repository root."""
    store = create_chunk_store(settings, client=client)
    return IncrementalIndexer(
        repo_root,
        parser_registry=create_default_parser_registry(),
        chunk_index=store,
    )
