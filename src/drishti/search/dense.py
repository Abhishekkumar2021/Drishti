"""Dense vector retriever (US-06.01)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drishti.embedding.dense import DenseEmbedder
from drishti.search.models import SearchHit
from drishti.search.qdrant_hits import point_to_search_hit
from drishti.storage.schema import DENSE_VECTOR_NAME

if TYPE_CHECKING:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter

logger = logging.getLogger(__name__)


class DenseVectorRetriever:
    """k-NN dense retrieval against a Qdrant named vector."""

    def __init__(
        self,
        client: QdrantClient,
        *,
        collection_name: str,
        embedder: DenseEmbedder,
        default_limit: int = 50,
    ) -> None:
        """Wire Qdrant client, collection, and dense embedder."""
        self._client = client
        self._collection = collection_name
        self._embedder = embedder
        self._default_limit = max(1, default_limit)

    def retrieve(
        self,
        query: str,
        *,
        filter_query: Filter | None = None,
        limit: int | None = None,
    ) -> list[SearchHit]:
        """Embed the query and return top dense neighbors with cosine scores."""
        if not query.strip():
            return []

        query_vector = self._embedder.embed_texts([query])[0]
        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            using=DENSE_VECTOR_NAME,
            query_filter=filter_query,
            limit=limit or self._default_limit,
            with_payload=True,
        )
        hits = [point_to_search_hit(point, source="dense") for point in response.points]
        logger.debug("Dense retrieval returned %s hits for query", len(hits))
        return hits
