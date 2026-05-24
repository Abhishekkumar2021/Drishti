"""Unit tests for chunk embedding pipeline."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from drishti.api.schemas import UniversalChunk
from drishti.embedding.dense import HashingDenseEmbedder
from drishti.embedding.pipeline import ChunkEmbeddingPipeline

pytestmark = pytest.mark.unit


def _sample_chunk(name: str = "run") -> UniversalChunk:
    return UniversalChunk(
        id="11111111-1111-4111-8111-111111111111",
        source_id="abc",
        content=f"def {name}():\n    return 1\n",
        content_type="code",
        file_path="sample.py",
        source_type="git_repo",
        language="python",
        start_line=1,
        end_line=2,
        node_type="function_definition",
        name=name,
        last_modified=datetime.now(UTC),
    )


class TestChunkEmbeddingPipeline:
    def test_embed_chunks_aligns_dense_and_sparse(self) -> None:
        pipeline = ChunkEmbeddingPipeline(HashingDenseEmbedder(dimensions=16))
        first = _sample_chunk("alpha")
        second = _sample_chunk("beta")
        second = second.model_copy(update={"id": "22222222-2222-4222-8222-222222222222"})
        chunks = [first, second]
        embedded = pipeline.embed_chunks(chunks)
        assert len(embedded) == 2
        assert len(embedded[0].dense) == 16
        assert embedded[0].sparse.indices
        assert embedded[0].chunk_id == chunks[0].id
