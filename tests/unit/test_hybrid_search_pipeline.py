"""Unit tests for the hybrid search pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from drishti.search.expansion import StaticQueryExpander
from drishti.search.models import SearchHit
from drishti.search.pipeline import HybridSearchPipeline
from drishti.search.rerank import LexicalReranker
from drishti.search.rrf import ReciprocalRankFusion

pytestmark = pytest.mark.unit


def _hit(chunk_id: str, content: str, *, source: str) -> SearchHit:
    return SearchHit(
        chunk_id=chunk_id,
        score=0.5,
        content=content,
        payload={"chunk_id": chunk_id},
        source=source,
    )


class TestHybridSearchPipeline:
    def test_runs_expand_retrieve_fuse_rerank(self) -> None:
        dense = MagicMock()
        sparse = MagicMock()
        dense.retrieve.return_value = [_hit("a", "widget", source="dense")]
        sparse.retrieve.return_value = [
            _hit("b", "validate auth token", source="sparse"),
        ]

        pipeline = HybridSearchPipeline(
            expander=StaticQueryExpander({"auth": ["token", "validate"]}),
            dense_retriever=dense,
            sparse_retriever=sparse,
            fusion=ReciprocalRankFusion(k=60),
            reranker=LexicalReranker(),
            retrieval_limit=50,
            default_top_k=1,
        )

        results = pipeline.search("auth", limit=1)

        assert len(results) == 1
        assert results[0].chunk_id == "b"
        dense.retrieve.assert_called_once()
        sparse.retrieve.assert_called_once()
        search_text = dense.retrieve.call_args.args[0]
        assert "token" in search_text
        assert "validate" in search_text
