"""Factory helpers for constructing hybrid search pipelines."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drishti.search.dense import DenseVectorRetriever
from drishti.search.expansion import (
    AnthropicQueryExpander,
    PassthroughQueryExpander,
    QueryExpander,
)
from drishti.search.pipeline import HybridSearchPipeline
from drishti.search.rerank import ChunkReranker, CohereReranker, LexicalReranker
from drishti.search.rrf import ReciprocalRankFusion
from drishti.search.sparse import SparseVectorRetriever

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

    from drishti.config import Settings
    from drishti.embedding.dense import DenseEmbedder
    from drishti.embedding.sparse import BM25SparseEncoder


def build_hybrid_search_pipeline(
    settings: Settings,
    *,
    client: QdrantClient,
    dense_embedder: DenseEmbedder,
    sparse_encoder: BM25SparseEncoder | None = None,
    expander: QueryExpander | None = None,
    reranker: ChunkReranker | None = None,
) -> HybridSearchPipeline:
    """Construct a ``HybridSearchPipeline`` from application settings."""
    collection = settings.qdrant_collection_name
    resolved_expander = expander or _default_expander(settings)
    resolved_reranker = reranker or _default_reranker(settings)

    return HybridSearchPipeline(
        expander=resolved_expander,
        dense_retriever=DenseVectorRetriever(
            client,
            collection_name=collection,
            embedder=dense_embedder,
            default_limit=settings.search_retrieval_limit,
        ),
        sparse_retriever=SparseVectorRetriever(
            client,
            collection_name=collection,
            sparse_encoder=sparse_encoder,
            default_limit=settings.search_retrieval_limit,
        ),
        fusion=ReciprocalRankFusion(k=settings.rrf_k),
        reranker=resolved_reranker,
        retrieval_limit=settings.search_retrieval_limit,
        default_top_k=settings.search_top_k,
    )


def _default_expander(settings: Settings) -> QueryExpander:
    if settings.anthropic_api_key.strip():
        return AnthropicQueryExpander(settings)
    return PassthroughQueryExpander()


def _default_reranker(settings: Settings) -> ChunkReranker:
    if settings.cohere_api_key.strip():
        return CohereReranker(settings, min_score=settings.rerank_min_score)
    return LexicalReranker()
