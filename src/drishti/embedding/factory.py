"""Factory for dense embedding backends."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drishti.embedding.cohere_dense import CohereDenseEmbedder
from drishti.embedding.dense import HashingDenseEmbedder, OpenAIDenseEmbeddingClient
from drishti.embedding.ollama_dense import OllamaDenseEmbedder
from drishti.embedding.openai_compatible import OpenAICompatibleDenseEmbedder
from drishti.exceptions import ConfigurationError

if TYPE_CHECKING:
    from drishti.config import Settings
    from drishti.embedding.dense import DenseEmbedder


def create_dense_embedder(settings: Settings) -> DenseEmbedder:
    """Instantiate a dense embedder from ``EMBEDDING_PROVIDER`` and related settings."""
    try:
        settings.validate_embedding_provider()
    except ValueError as exc:
        raise ConfigurationError(str(exc)) from exc
    provider = settings.embedding_provider

    if provider == "hashing":
        return HashingDenseEmbedder(dimensions=settings.resolved_embedding_dimensions())

    if provider == "openai":
        return OpenAIDenseEmbeddingClient(settings)

    if provider == "openai_compatible":
        return OpenAICompatibleDenseEmbedder(settings)

    if provider == "cohere":
        return CohereDenseEmbedder(settings)

    if provider == "ollama":
        return OllamaDenseEmbedder(settings)

    msg = f"Unsupported embedding provider: {provider}"
    raise ConfigurationError(msg)
