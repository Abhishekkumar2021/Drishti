"""Dense embedding clients (US-05.01)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Protocol

from openai import OpenAI

if TYPE_CHECKING:
    from drishti.config import Settings


class DenseEmbedder(Protocol):
    """Protocol for dense text embedding backends."""

    @property
    def dimensions(self) -> int:
        """Return embedding vector dimensionality."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into dense vectors."""


class OpenAIDenseEmbeddingClient:
    """Generates dense embeddings via OpenAI (delegates to OpenAI-compatible client)."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: OpenAI | None = None,
        batch_size: int = 64,
        max_retries: int = 5,
    ) -> None:
        """Initialize the embedding client from application settings."""
        from drishti.embedding.openai_compatible import OpenAICompatibleDenseEmbedder

        self._delegate = OpenAICompatibleDenseEmbedder(
            settings,
            client=client,
            batch_size=batch_size,
            max_retries=max_retries,
        )

    @property
    def dimensions(self) -> int:
        """Return embedding vector dimensionality."""
        return self._delegate.dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in batches with retry on transient API failures."""
        return self._delegate.embed_texts(texts)


class HashingDenseEmbedder:
    """Deterministic dense embedder for tests and integration without external APIs."""

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
