"""OpenAI-compatible dense embedding client (OpenAI, Azure, vLLM, LiteLLM, Ollama)."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from drishti.exceptions import EmbeddingError

if TYPE_CHECKING:
    from drishti.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_BATCH_SIZE = 64
_DEFAULT_MAX_RETRIES = 5
_DEFAULT_RETRY_BASE_SECONDS = 0.5


class OpenAICompatibleDenseEmbedder:
    """Dense embeddings via any OpenAI-compatible ``/v1/embeddings`` endpoint."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: OpenAI | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize from settings (model, dimensions, base URL, API key)."""
        self._dimensions = settings.resolved_embedding_dimensions()
        self._model = settings.resolved_embedding_model()
        self._batch_size = max(1, batch_size)
        self._max_retries = max(1, max_retries)
        api_key = settings.api_key_for_embedding_provider()
        api_base = settings.resolved_embedding_api_base()
        if client is None and settings.embedding_provider == "openai_compatible" and not api_base:
            msg = "EMBEDDING_API_BASE is required when EMBEDDING_PROVIDER=openai_compatible"
            raise EmbeddingError(msg)
        if client is None and not api_key.strip():
            msg = "API key required for embeddings (OPENAI_API_KEY or EMBEDDING_API_KEY)"
            raise EmbeddingError(msg)
        if client is not None:
            self._client = client
        else:
            base_url = None
            if api_base:
                base_url = f"{api_base}/v1" if not api_base.endswith("/v1") else api_base
            if base_url:
                self._client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self._client = OpenAI(api_key=api_key)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
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
                kwargs: dict[str, Any] = {
                    "model": self._model,
                    "input": batch,
                }
                if self._dimensions > 0 and self._model.startswith("text-embedding-3"):
                    kwargs["dimensions"] = self._dimensions
                response = self._client.embeddings.create(**kwargs)
                ordered = sorted(response.data, key=lambda item: item.index)
                vectors = [list(item.embedding) for item in ordered]
                if self._dimensions > 0 and vectors and len(vectors[0]) != self._dimensions:
                    msg = (
                        f"Embedding dimension mismatch: expected {self._dimensions}, "
                        f"got {len(vectors[0])} for model {self._model}"
                    )
                    raise EmbeddingError(msg)
                return vectors
            except (RateLimitError, APIConnectionError, APIStatusError) as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    break
                delay = _DEFAULT_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "Embedding attempt %s/%s failed; retrying in %.1fs",
                    attempt,
                    self._max_retries,
                    delay,
                )
                time.sleep(delay)
        msg = f"Embedding request failed after {self._max_retries} attempts"
        raise EmbeddingError(msg) from last_error
