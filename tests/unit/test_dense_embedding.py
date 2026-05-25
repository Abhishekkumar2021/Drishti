"""Unit tests for OpenAI dense embeddings (US-05.01)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from drishti.config import Settings
from drishti.embedding.dense import HashingDenseEmbedder, OpenAIDenseEmbeddingClient
from drishti.exceptions import EmbeddingError

pytestmark = pytest.mark.unit


class TestOpenAIDenseEmbeddingClient:
    def test_embed_texts_returns_1536_dimensions(self) -> None:
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = SimpleNamespace(
            data=[
                SimpleNamespace(index=0, embedding=[0.1] * 1536),
                SimpleNamespace(index=1, embedding=[0.2] * 1536),
            ]
        )
        settings = Settings(
            _env_file=None,
            embedding_provider="openai",
            openai_api_key="test-key",
            openai_embedding_dimensions=1536,
        )
        client = OpenAIDenseEmbeddingClient(settings, client=mock_client)

        vectors = client.embed_texts(["alpha", "beta"])

        assert len(vectors) == 2
        assert len(vectors[0]) == 1536
        mock_client.embeddings.create.assert_called_once()

    def test_requires_api_key_when_client_not_injected(self) -> None:
        settings = Settings(_env_file=None, embedding_provider="openai", openai_api_key="")
        with pytest.raises(EmbeddingError, match=r"API key"):
            OpenAIDenseEmbeddingClient(settings)

    def test_batches_large_inputs(self) -> None:
        mock_client = MagicMock()
        first_batch = [
            SimpleNamespace(index=index, embedding=[float(index)] * 8) for index in range(64)
        ]
        mock_client.embeddings.create.side_effect = [
            SimpleNamespace(data=first_batch),
            SimpleNamespace(
                data=[SimpleNamespace(index=0, embedding=[1.0] * 8)],
            ),
        ]
        settings = Settings(
            _env_file=None,
            embedding_provider="openai",
            openai_api_key="test-key",
            openai_embedding_dimensions=8,
        )
        client = OpenAIDenseEmbeddingClient(settings, client=mock_client, batch_size=64)
        vectors = client.embed_texts(["x"] * 65)
        assert len(vectors) == 65
        assert mock_client.embeddings.create.call_count == 2


class TestHashingDenseEmbedder:
    def test_produces_normalized_vectors(self) -> None:
        embedder = HashingDenseEmbedder(dimensions=16)
        vectors = embedder.embed_texts(["same", "same", "other"])
        assert len(vectors[0]) == 16
        assert vectors[0] == vectors[1]
        assert vectors[0] != vectors[2]
