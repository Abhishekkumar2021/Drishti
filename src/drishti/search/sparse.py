"""Sparse BM25 retriever (US-06.02)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from qdrant_client.models import SparseVector

from drishti.embedding.sparse import BM25SparseEncoder
from drishti.search.models import SearchHit
from drishti.search.qdrant_hits import point_to_search_hit
from drishti.storage.schema import SPARSE_VECTOR_NAME

if TYPE_CHECKING:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter

logger = logging.getLogger(__name__)


class SparseVectorRetriever:
    """Sparse vector retrieval using BM25-encoded queries."""

    def __init__(
        self,
        client: QdrantClient,
        *,
        collection_name: str,
        sparse_encoder: BM25SparseEncoder | None = None,
        default_limit: int = 50,
    ) -> None:
        """Wire Qdrant client, collection, and sparse encoder."""
        self._client = client
        self._collection = collection_name
        self._sparse = sparse_encoder or BM25SparseEncoder()
        self._default_limit = max(1, default_limit)

    def retrieve(
        self,
        query: str,
        *,
        filter_query: Filter | None = None,
        limit: int | None = None,
    ) -> list[SearchHit]:
        """Encode the query as sparse BM25 weights and search Qdrant."""
        if not query.strip():
            return []

        if self._sparse.vocabulary_size > 0:
            encoded = self._sparse.encode(query)
        else:
            encoded = self._sparse.encode_many([query])[0]
        if not encoded.indices:
            return []

        response = self._client.query_points(
            collection_name=self._collection,
            query=SparseVector(indices=encoded.indices, values=encoded.values),
            using=SPARSE_VECTOR_NAME,
            query_filter=filter_query,
            limit=limit or self._default_limit,
            with_payload=True,
        )
        hits = [point_to_search_hit(point, source="sparse") for point in response.points]
        logger.debug("Sparse retrieval returned %s hits for query", len(hits))
        return hits
