"""Integration tests for Qdrant vector storage read/write cycles."""

from __future__ import annotations

import uuid

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from drishti.config import Settings

pytestmark = pytest.mark.integration


class TestQdrantStorage:
    def test_collection_upsert_and_retrieve(
        self,
        integration_settings: Settings,
        qdrant_client: QdrantClient,
    ) -> None:
        collection_name = f"drishti_it_{uuid.uuid4().hex[:12]}"
        vector = [0.1, 0.2, 0.3, 0.4]
        payload = {"symbol": "AuthService", "language": "java"}

        try:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=len(vector), distance=Distance.COSINE),
            )
            qdrant_client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=1,
                        vector=vector,
                        payload=payload,
                    ),
                ],
            )

            records, _next = qdrant_client.scroll(
                collection_name=collection_name,
                limit=10,
                with_payload=True,
                with_vectors=True,
            )
            assert len(records) == 1
            assert records[0].payload == payload
            assert records[0].vector is not None
            assert len(records[0].vector) == len(vector)

            info = qdrant_client.get_collection(collection_name=collection_name)
            assert info.points_count == 1
        finally:
            qdrant_client.delete_collection(collection_name=collection_name, timeout=30)

    def test_lists_collections(self, qdrant_client: QdrantClient) -> None:
        collections = qdrant_client.get_collections()
        assert collections is not None
