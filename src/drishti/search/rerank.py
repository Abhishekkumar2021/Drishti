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
        settings: Settings | None = None,
        *,
        min_score: float = 0.0,
        model: str | None = None,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        """Initialize the Cohere client from settings or explicit overrides."""
        if settings is not None:
            self._model = model or settings.resolved_rerank_model()
            resolved_key = (
                api_key if api_key is not None else settings.api_key_for_rerank_provider()
            )
        else:
            if not model or api_key is None:
                msg = "CohereReranker requires settings or explicit model and api_key"
                raise SearchError(msg)
            self._model = model
            resolved_key = api_key
        self._min_score = min_score
        if client is None and not resolved_key.strip():
            msg = "COHERE_API_KEY is required for Cohere re-ranking"
            raise SearchError(msg)
        if client is not None:
            self._client: Any = client
        else:
            import cohere

            self._client = cohere.Client(api_key=resolved_key)

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
