"""Unit tests for dense vector retrieval (US-06.01)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from drishti.embedding.dense import HashingDenseEmbedder
from drishti.search.dense import DenseVectorRetriever

pytestmark = pytest.mark.unit


class TestDenseVectorRetriever:
    def test_embeds_query_and_queries_qdrant(self) -> None:
        mock_client = MagicMock()
        mock_client.query_points.return_value = SimpleNamespace(
            points=[
                SimpleNamespace(
                    id="p1",
                    score=0.88,
                    payload={"chunk_id": "c1", "content": "def validate(): pass"},
                )
            ]
        )
        embedder = HashingDenseEmbedder(dimensions=8)
        retriever = DenseVectorRetriever(
            mock_client,
            collection_name="chunks",
            embedder=embedder,
            default_limit=5,
        )

        hits = retriever.retrieve("validate token")

        assert len(hits) == 1
        assert hits[0].chunk_id == "c1"
        assert hits[0].source == "dense"
        assert hits[0].score == pytest.approx(0.88)
        mock_client.query_points.assert_called_once()
        call_kwargs = mock_client.query_points.call_args.kwargs
        assert call_kwargs["using"] == "dense"
        assert len(call_kwargs["query"]) == 8
