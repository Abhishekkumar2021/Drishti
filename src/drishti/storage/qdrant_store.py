"""Qdrant-backed chunk index (US-05.03)."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    SparseVector,
)

from drishti.embedding.pipeline import ChunkEmbeddingPipeline
from drishti.ingestion.chunk_index import ChunkIndex
from drishti.storage.schema import DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME, ensure_chunk_collection

if TYPE_CHECKING:
    from drishti.api.schemas import UniversalChunk
    from drishti.config import Settings

logger = logging.getLogger(__name__)


class QdrantChunkStore(ChunkIndex):
    """Persists embedded universal chunks in a Qdrant hybrid collection."""

    def __init__(
        self,
        settings: Settings,
        embedding_pipeline: ChunkEmbeddingPipeline,
        *,
        client: QdrantClient | None = None,
    ) -> None:
        """Initialize the store and ensure the target collection exists."""
        self._collection = settings.qdrant_collection_name
        self._pipeline = embedding_pipeline
        timeout_seconds = int(settings.health_check_timeout_seconds)
        self._client = client or QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=timeout_seconds,
            check_compatibility=False,
        )
        ensure_chunk_collection(
            self._client,
            collection_name=self._collection,
            dense_dimensions=embedding_pipeline.dense_dimensions,
        )

    def upsert(self, chunks: list[UniversalChunk]) -> int:
        """Embed and upsert chunks; return number of points written."""
        if not chunks:
            return 0

        embedded = self._pipeline.embed_chunks(chunks)
        chunk_by_id = {chunk.id: chunk for chunk in chunks}
        points: list[PointStruct] = []

        for vectors in embedded:
            chunk = chunk_by_id[vectors.chunk_id]
            points.append(
                PointStruct(
                    id=_point_id(chunk.id),
                    vector={
                        DENSE_VECTOR_NAME: vectors.dense,
                        SPARSE_VECTOR_NAME: SparseVector(
                            indices=vectors.sparse.indices,
                            values=vectors.sparse.values,
                        ),
                    },
                    payload=_chunk_payload(chunk),
                )
            )

        self._client.upsert(collection_name=self._collection, points=points, wait=True)
        return len(points)

    def delete_by_file_paths(self, file_paths: Iterable[str]) -> int:
        """Delete all points whose payload ``file_path`` matches."""
        paths = list(file_paths)
        if not paths:
            return 0

        total_removed = 0
        for file_path in paths:
            filter_query = Filter(
                must=[
                    FieldCondition(
                        key="file_path",
                        match=MatchValue(value=file_path),
                    )
                ]
            )
            records, _next = self._client.scroll(
                collection_name=self._collection,
                scroll_filter=filter_query,
                limit=10_000,
                with_payload=False,
            )
            if not records:
                continue
            self._client.delete(
                collection_name=self._collection,
                points_selector=FilterSelector(filter=filter_query),
                wait=True,
            )
            total_removed += len(records)
        return total_removed

    def count(self) -> int:
        """Return the number of points in the collection."""
        info = self._client.get_collection(collection_name=self._collection)
        return int(info.points_count or 0)

    def scroll_payloads(
        self,
        *,
        limit: int = 100,
        filter_query: Filter | None = None,
    ) -> list[dict[str, Any]]:
        """Scroll payloads for integration tests and diagnostics."""
        records, _next = self._client.scroll(
            collection_name=self._collection,
            limit=limit,
            scroll_filter=filter_query,
            with_payload=True,
            with_vectors=False,
        )
        payloads: list[dict[str, Any]] = []
        for record in records:
            if record.payload:
                payloads.append(dict(record.payload))
        return payloads


def _chunk_payload(chunk: UniversalChunk) -> dict[str, Any]:
    payload = chunk.model_dump(mode="json")
    payload["chunk_id"] = chunk.id
    return payload


def _point_id(chunk_id: str) -> str:
    return str(uuid.UUID(chunk_id))
