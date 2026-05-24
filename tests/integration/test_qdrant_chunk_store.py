"""Integration tests for Qdrant hybrid chunk storage (EPIC-05)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from qdrant_client import QdrantClient

from drishti.api.schemas import UniversalChunk
from drishti.config import Settings
from drishti.embedding.dense import HashingDenseEmbedder
from drishti.embedding.pipeline import ChunkEmbeddingPipeline
from drishti.storage.filters import compile_qdrant_filter
from drishti.storage.qdrant_store import QdrantChunkStore
from drishti.storage.schema import DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME, ensure_chunk_collection

pytestmark = pytest.mark.integration


def _chunk(*, file_path: str, name: str, content: str) -> UniversalChunk:
    return UniversalChunk(
        id=str(uuid.uuid4()),
        source_id="hash",
        content=content,
        content_type="code",
        file_path=file_path,
        source_type="git_repo",
        language="python",
        start_line=1,
        end_line=3,
        node_type="function_definition",
        name=name,
        last_modified=datetime.now(UTC),
    )


class TestQdrantChunkStoreIntegration:
    def test_hybrid_upsert_filter_and_delete_cycle(
        self,
        integration_settings: Settings,
        qdrant_client: QdrantClient,
    ) -> None:
        collection_name = f"drishti_it_{uuid.uuid4().hex[:12]}"
        dimensions = 16
        settings = integration_settings.model_copy(
            update={
                "qdrant_collection_name": collection_name,
                "openai_embedding_dimensions": dimensions,
            }
        )
        ensure_chunk_collection(
            qdrant_client,
            collection_name=collection_name,
            dense_dimensions=dimensions,
            recreate=True,
        )

        pipeline = ChunkEmbeddingPipeline(HashingDenseEmbedder(dimensions=dimensions))
        store = QdrantChunkStore(settings, pipeline, client=qdrant_client)

        chunks = [
            _chunk(
                file_path="src/auth/service.py",
                name="AuthService",
                content="class AuthService:\n    def validate(self):\n        return True\n",
            ),
            _chunk(
                file_path="src/auth/token.py",
                name="validate",
                content="def validate(token: str) -> bool:\n    return bool(token)\n",
            ),
        ]

        try:
            indexed = store.upsert(chunks)
            assert indexed == 2
            assert store.count() == 2

            info = qdrant_client.get_collection(collection_name=collection_name)
            assert info.config.params.vectors is not None
            assert DENSE_VECTOR_NAME in info.config.params.vectors
            assert info.config.params.sparse_vectors is not None
            assert SPARSE_VECTOR_NAME in info.config.params.sparse_vectors

            filtered = store.scroll_payloads(
                limit=10,
                filter_query=compile_qdrant_filter({"file_path": "src/auth/*"}),
            )
            assert len(filtered) == 2

            removed = store.delete_by_file_paths(["src/auth/token.py"])
            assert removed == 1
            assert store.count() == 1
        finally:
            qdrant_client.delete_collection(collection_name=collection_name, timeout=30)
