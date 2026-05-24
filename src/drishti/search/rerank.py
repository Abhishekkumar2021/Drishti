"""Cohere cross-encoder re-ranking (US-06.04)."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Protocol

from drishti.exceptions import SearchError
from drishti.search.models import SearchHit

if TYPE_CHECKING:
    from drishti.config import Settings

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"\w+")


class ChunkReranker(Protocol):
    """Protocol for re-ranking fused search candidates."""

    def rerank(
        self,
        query: str,
        candidates: list[SearchHit],
        *,
        top_n: int,
    ) -> list[SearchHit]:
        """Return candidates re-ordered by relevance to the query."""


class CohereReranker:
    """Re-rank candidates via the Cohere rerank API."""

    def __init__(
        self,
        settings: Settings,
        *,
        min_score: float = 0.0,
        client: Any | None = None,
    ) -> None:
        """Initialize the Cohere client from settings."""
        self._model = settings.cohere_rerank_model
        self._min_score = min_score
        api_key = settings.cohere_api_key.strip()
        if client is None and not api_key:
            msg = "COHERE_API_KEY is required for Cohere re-ranking"
            raise SearchError(msg)
        if client is not None:
            self._client: Any = client
        else:
            import cohere

            self._client = cohere.Client(api_key=api_key)

    def rerank(
        self,
        query: str,
        candidates: list[SearchHit],
        *,
        top_n: int,
    ) -> list[SearchHit]:
        """Send candidates to Cohere and return top matches above ``min_score``."""
        if not candidates:
            return []

        documents = [candidate.content for candidate in candidates]
        response = self._client.rerank(
            model=self._model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents)),
        )

        reranked: list[SearchHit] = []
        for result in response.results:
            if result.relevance_score < self._min_score:
                continue
            candidate = candidates[result.index]
            reranked.append(
                candidate.with_score(float(result.relevance_score), source="rerank"),
            )
        return reranked


class LexicalReranker:
    """Deterministic lexical reranker for unit and integration tests."""

    def rerank(
        self,
        query: str,
        candidates: list[SearchHit],
        *,
        top_n: int,
    ) -> list[SearchHit]:
        """Score candidates by query token overlap in chunk content."""
        if not candidates:
            return []

        query_tokens = {token.lower() for token in _TOKEN_RE.findall(query)}
        scored: list[tuple[float, SearchHit]] = []
        for candidate in candidates:
            content_tokens = {token.lower() for token in _TOKEN_RE.findall(candidate.content)}
            overlap = len(query_tokens & content_tokens)
            score = overlap / max(len(query_tokens), 1)
            scored.append((score, candidate.with_score(score, source="rerank")))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [hit for score, hit in scored[:top_n] if score > 0] or [
            hit for _, hit in scored[:top_n]
        ]
