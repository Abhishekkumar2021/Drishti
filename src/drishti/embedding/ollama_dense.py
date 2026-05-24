"""Ollama dense embedding client."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from drishti.exceptions import EmbeddingError

if TYPE_CHECKING:
    from drishti.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 60.0


class OllamaDenseEmbedder:
    """Dense embeddings via Ollama ``/api/embeddings``."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._model = settings.resolved_embedding_model()
        self._dimensions = settings.resolved_embedding_dimensions()
        self._api_base = settings.resolved_embedding_api_base().rstrip("/")
        self._client = client or httpx.Client(timeout=timeout_seconds)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            response = self._client.post(
                f"{self._api_base}/api/embeddings",
                json={"model": self._model, "prompt": text},
            )
            response.raise_for_status()
            data = response.json()
            embedding = list(data.get("embedding") or [])
            if not embedding:
                msg = f"Ollama returned empty embedding for model {self._model}"
                raise EmbeddingError(msg)
            if self._dimensions > 0 and len(embedding) != self._dimensions:
                msg = (
                    f"Embedding dimension mismatch: expected {self._dimensions}, "
                    f"got {len(embedding)} for model {self._model}"
                )
                raise EmbeddingError(msg)
            vectors.append(embedding)
        return vectors
