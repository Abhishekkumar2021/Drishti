"""OpenAI dense embedding client (US-05.01)."""

from __future__ import annotations

import logging
import math
import time
from typing import TYPE_CHECKING, Protocol

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from drishti.exceptions import EmbeddingError

if TYPE_CHECKING:
    from drishti.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_BATCH_SIZE = 64
_DEFAULT_MAX_RETRIES = 5
_DEFAULT_RETRY_BASE_SECONDS = 0.5


class DenseEmbedder(Protocol):
    """Protocol for dense text embedding backends."""

    @property
    def dimensions(self) -> int:
        """Return embedding vector dimensionality."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into dense vectors."""


class OpenAIDenseEmbeddingClient:
    """Generates dense embeddings via OpenAI ``text-embedding-3-small``."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: OpenAI | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize the embedding client from application settings."""
        self._dimensions = settings.openai_embedding_dimensions
        self._model = settings.openai_embedding_model
        self._batch_size = max(1, batch_size)
        self._max_retries = max(1, max_retries)
        api_key = settings.openai_api_key.strip()
        if client is None and not api_key:
            msg = "OPENAI_API_KEY is required for dense embeddings"
            raise EmbeddingError(msg)
        self._client = client or OpenAI(api_key=api_key)

    @property
    def dimensions(self) -> int:
        """Return embedding vector dimensionality."""
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in batches with retry on transient API failures."""
        if not texts:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            vectors.extend(self._embed_batch_with_retry(batch))
        return vectors

    def _embed_batch_with_retry(self, batch: list[str]) -> list[list[float]]:
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                    dimensions=self._dimensions,
                )
                ordered = sorted(response.data, key=lambda item: item.index)
                return [list(item.embedding) for item in ordered]
            except (RateLimitError, APIConnectionError, APIStatusError) as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    break
                delay = _DEFAULT_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "OpenAI embedding attempt %s/%s failed; retrying in %.1fs",
                    attempt,
                    self._max_retries,
                    delay,
                )
                time.sleep(delay)
        msg = f"OpenAI embedding request failed after {self._max_retries} attempts"
        raise EmbeddingError(msg) from last_error


class HashingDenseEmbedder:
    """Deterministic dense embedder for tests and integration without OpenAI."""

    def __init__(self, *, dimensions: int = 1536) -> None:
        """Initialize with the target vector dimensionality."""
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        """Return embedding vector dimensionality."""
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Map text to a normalized pseudo-random dense vector."""
        return [self._hash_to_vector(text) for text in texts]

    def _hash_to_vector(self, text: str) -> list[float]:
        import hashlib

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        seed = digest
        while len(values) < self._dimensions:
            for byte in seed:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) >= self._dimensions:
                    break
            seed = hashlib.sha256(seed).digest()
        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            return values
        return [value / norm for value in values]
