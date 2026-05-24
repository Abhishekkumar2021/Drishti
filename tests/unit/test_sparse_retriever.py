"""Unit tests for sparse vector retrieval (US-06.02)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qdrant_client.models import SparseVector

from drishti.search.sparse import SparseVectorRetriever

pytestmark = pytest.mark.unit


class TestSparseVectorRetriever:
    def test_encodes_query_and_queries_sparse_vector(self) -> None:
        mock_client = MagicMock()
        mock_client.query_points.return_value = SimpleNamespace(
            points=[
                SimpleNamespace(
                    id="p1",
                    score=1.2,
                    payload={"chunk_id": "c2", "content": "AuthService"},
                )
            ]
        )
        retriever = SparseVectorRetriever(
            mock_client,
            collection_name="chunks",
            default_limit=5,
        )

        hits = retriever.retrieve("AuthService validate")

        assert len(hits) == 1
        assert hits[0].chunk_id == "c2"
        assert hits[0].source == "sparse"
        call_kwargs = mock_client.query_points.call_args.kwargs
        assert call_kwargs["using"] == "sparse"
        assert isinstance(call_kwargs["query"], SparseVector)
