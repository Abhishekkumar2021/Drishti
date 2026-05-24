"""Integration tests for hybrid search against Qdrant (EPIC-06)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from qdrant_client import QdrantClient

from drishti.api.schemas import UniversalChunk
from drishti.config import Settings
from drishti.embedding.dense import HashingDenseEmbedder
from drishti.embedding.pipeline import ChunkEmbeddingPipeline
from drishti.embedding.sparse import BM25SparseEncoder
from drishti.search.dense import DenseVectorRetriever
from drishti.search.expansion import PassthroughQueryExpander
from drishti.search.pipeline import HybridSearchPipeline
from drishti.search.rerank import LexicalReranker
from drishti.search.rrf import ReciprocalRankFusion
from drishti.search.sparse import SparseVectorRetriever
from drishti.storage.qdrant_store import QdrantChunkStore
from drishti.storage.schema import ensure_chunk_collection

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


class TestHybridSearchIntegration:
    def test_hybrid_search_returns_matching_chunk(
        self,
        integration_settings: Settings,
        qdrant_client: QdrantClient,
    ) -> None:
        collection_name = f"drishti_search_{uuid.uuid4().hex[:12]}"
        dimensions = 16
        settings = integration_settings.model_copy(
            update={
                "qdrant_collection_name": collection_name,
                "openai_embedding_dimensions": dimensions,
                "search_retrieval_limit": 10,
                "search_top_k": 3,
            }
        )
        ensure_chunk_collection(
            qdrant_client,
            collection_name=collection_name,
            dense_dimensions=dimensions,
            recreate=True,
        )

        embedder = HashingDenseEmbedder(dimensions=dimensions)
        sparse_encoder = BM25SparseEncoder()
        pipeline = ChunkEmbeddingPipeline(embedder, sparse_encoder=sparse_encoder)
        store = QdrantChunkStore(settings, pipeline, client=qdrant_client)

        chunks = [
            _chunk(
                file_path="src/ui/widget.py",
                name="Widget",
                content="class Widget:\n    pass\n",
            ),
            _chunk(
                file_path="src/auth/token.py",
                name="validate",
                content="def validate(token: str) -> bool:\n    return bool(token)\n",
            ),
        ]

        search_pipeline = HybridSearchPipeline(
            expander=PassthroughQueryExpander(),
            dense_retriever=DenseVectorRetriever(
                qdrant_client,
                collection_name=collection_name,
                embedder=embedder,
                default_limit=settings.search_retrieval_limit,
            ),
            sparse_retriever=SparseVectorRetriever(
                qdrant_client,
                collection_name=collection_name,
                sparse_encoder=sparse_encoder,
                default_limit=settings.search_retrieval_limit,
            ),
            fusion=ReciprocalRankFusion(k=settings.rrf_k),
            reranker=LexicalReranker(),
            retrieval_limit=settings.search_retrieval_limit,
            default_top_k=settings.search_top_k,
        )

        try:
            assert store.upsert(chunks) == 2

            results = search_pipeline.search(
                "validate token",
                filters={"file_path": "src/auth/*"},
                limit=1,
            )

            assert len(results) == 1
            assert results[0].chunk_id == chunks[1].id
            assert "validate" in results[0].content
        finally:
            qdrant_client.delete_collection(collection_name=collection_name, timeout=30)
