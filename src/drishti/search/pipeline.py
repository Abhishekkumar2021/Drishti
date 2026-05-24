"""Hybrid search pipeline orchestrating retrieval, fusion, and reranking."""

from __future__ import annotations

import logging

from drishti.search.dense import DenseVectorRetriever
from drishti.search.expansion import QueryExpander, combine_expanded_query
from drishti.search.models import SearchHit
from drishti.search.rerank import ChunkReranker
from drishti.search.rrf import ReciprocalRankFusion
from drishti.search.sparse import SparseVectorRetriever
from drishti.storage.filters import compile_qdrant_filter

logger = logging.getLogger(__name__)


class HybridSearchPipeline:
    """End-to-end hybrid search: expand → dense/sparse → RRF → rerank."""

    def __init__(
        self,
        *,
        expander: QueryExpander,
        dense_retriever: DenseVectorRetriever,
        sparse_retriever: SparseVectorRetriever,
        fusion: ReciprocalRankFusion,
        reranker: ChunkReranker,
        retrieval_limit: int = 50,
        default_top_k: int = 10,
    ) -> None:
        """Wire pipeline stages."""
        self._expander = expander
        self._dense = dense_retriever
        self._sparse = sparse_retriever
        self._fusion = fusion
        self._reranker = reranker
        self._retrieval_limit = max(1, retrieval_limit)
        self._default_top_k = max(1, default_top_k)

    def search(
        self,
        query: str,
        *,
        filters: dict[str, str] | None = None,
        limit: int | None = None,
    ) -> list[SearchHit]:
        """Run hybrid search and return reranked chunk hits."""
        stripped = query.strip()
        if not stripped:
            return []

        expanded_terms = self._expander.expand(stripped)
        search_text = combine_expanded_query(expanded_terms)
        filter_query = compile_qdrant_filter(filters)
        top_k = limit or self._default_top_k

        dense_hits = self._dense.retrieve(
            search_text,
            filter_query=filter_query,
            limit=self._retrieval_limit,
        )
        sparse_hits = self._sparse.retrieve(
            search_text,
            filter_query=filter_query,
            limit=self._retrieval_limit,
        )
        fused = self._fusion.merge(dense_hits, sparse_hits)
        reranked = self._reranker.rerank(stripped, fused, top_n=top_k)
        logger.info(
            "Hybrid search for %r: dense=%s sparse=%s fused=%s reranked=%s",
            stripped,
            len(dense_hits),
            len(sparse_hits),
            len(fused),
            len(reranked),
        )
        return reranked
