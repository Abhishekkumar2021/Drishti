"""Unit tests for re-ranking (US-06.04)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from drishti.config import Settings
from drishti.exceptions import SearchError
from drishti.search.models import SearchHit
from drishti.search.rerank import CohereReranker, LexicalReranker

pytestmark = pytest.mark.unit


def _hit(chunk_id: str, content: str) -> SearchHit:
    return SearchHit(
        chunk_id=chunk_id,
        score=0.5,
        content=content,
        payload={"chunk_id": chunk_id},
        source="rrf",
    )


class TestCohereReranker:
    def test_rerank_orders_by_relevance_score(self) -> None:
        mock_client = MagicMock()
        mock_client.rerank.return_value = SimpleNamespace(
            results=[
                SimpleNamespace(index=1, relevance_score=0.92),
                SimpleNamespace(index=0, relevance_score=0.41),
            ]
        )
        settings = Settings(cohere_api_key="test-key")
        reranker = CohereReranker(settings, client=mock_client, min_score=0.0)
        candidates = [
            _hit("a", "unrelated"),
            _hit("b", "validate auth token"),
        ]

        results = reranker.rerank("auth token", candidates, top_n=2)

        assert [hit.chunk_id for hit in results] == ["b", "a"]
        assert results[0].score == pytest.approx(0.92)
        assert results[0].source == "rerank"

    def test_filters_below_min_score(self) -> None:
        mock_client = MagicMock()
        mock_client.rerank.return_value = SimpleNamespace(
            results=[SimpleNamespace(index=0, relevance_score=0.2)]
        )
        settings = Settings(cohere_api_key="test-key")
        reranker = CohereReranker(settings, client=mock_client, min_score=0.5)
        candidates = [_hit("a", "content")]

        assert reranker.rerank("query", candidates, top_n=5) == []

    def test_requires_api_key_when_client_not_injected(self) -> None:
        settings = Settings(cohere_api_key="")
        with pytest.raises(SearchError, match="COHERE_API_KEY"):
            CohereReranker(settings)


class TestLexicalReranker:
    def test_prefers_token_overlap(self) -> None:
        reranker = LexicalReranker()
        candidates = [
            _hit("a", "class Widget {}"),
            _hit("b", "def validate(token): return True"),
        ]

        results = reranker.rerank("validate token", candidates, top_n=1)

        assert results[0].chunk_id == "b"
