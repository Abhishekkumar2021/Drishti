"""Cohere dense embedding client."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from drishti.exceptions import EmbeddingError

if TYPE_CHECKING:
    from drishti.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_BATCH_SIZE = 96


class CohereDenseEmbedder:
    """Dense embeddings via the Cohere Embed API."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: Any | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> None:
        self._dimensions = settings.resolved_embedding_dimensions()
        self._model = settings.resolved_embedding_model()
        self._batch_size = max(1, batch_size)
        api_key = settings.api_key_for_embedding_provider()
        if client is None and not api_key:
            msg = "COHERE_API_KEY or EMBEDDING_API_KEY is required for Cohere embeddings"
            raise EmbeddingError(msg)
        if client is not None:
            self._client: Any = client
        else:
            import cohere

            self._client = cohere.Client(api_key=api_key)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            response = self._client.embed(
                texts=batch,
                model=self._model,
                input_type="search_document",
                embedding_types=["float"],
            )
            batch_vectors = [list(item) for item in response.embeddings.float]
            vectors.extend(batch_vectors)
        if self._dimensions > 0 and vectors and len(vectors[0]) != self._dimensions:
            msg = (
                f"Embedding dimension mismatch: expected {self._dimensions}, "
                f"got {len(vectors[0])} for model {self._model}"
            )
            raise EmbeddingError(msg)
        return vectors
