"""Unit tests for provider-agnostic LLM and embedding factories."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from drishti.config import Settings
from drishti.embedding.cohere_dense import CohereDenseEmbedder
from drishti.embedding.dense import HashingDenseEmbedder, OpenAIDenseEmbeddingClient
from drishti.embedding.factory import create_dense_embedder
from drishti.embedding.ollama_dense import OllamaDenseEmbedder
from drishti.embedding.openai_compatible import OpenAICompatibleDenseEmbedder
from drishti.exceptions import ConfigurationError, EmbeddingError
from drishti.generation.factory import create_chat_llm
from drishti.generation.llm import AnthropicChatLLM, MockChatLLM, OllamaChatLLM, OpenAIChatLLM
from drishti.search.expansion import LLMQueryExpander

pytestmark = pytest.mark.unit


class TestSettingsResolution:
    def test_resolved_embedding_model_explicit(self) -> None:
        settings = Settings(
            embedding_provider="openai",
            embedding_model="text-embedding-3-large",
        )
        assert settings.resolved_embedding_model() == "text-embedding-3-large"

    def test_resolved_llm_model_explicit(self) -> None:
        settings = Settings(llm_provider="openai", llm_model="gpt-4o")
        assert settings.resolved_llm_model() == "gpt-4o"

    def test_api_key_override(self) -> None:
        settings = Settings(
            embedding_api_key="shared-key",
            openai_api_key="openai-key",
        )
        assert settings.api_key_for_embedding_provider() == "shared-key"


class TestCreateDenseEmbedder:
    def test_openai_provider(self) -> None:
        settings = Settings(embedding_provider="openai", openai_api_key="key")
        embedder = create_dense_embedder(settings)
        assert isinstance(embedder, OpenAIDenseEmbeddingClient)

    def test_hashing_provider(self) -> None:
        settings = Settings(embedding_provider="hashing", embedding_dimensions=32)
        embedder = create_dense_embedder(settings)
        assert isinstance(embedder, HashingDenseEmbedder)
        assert embedder.dimensions == 32

    def test_cohere_provider(self) -> None:
        settings = Settings(embedding_provider="cohere", cohere_api_key="key")
        embedder = create_dense_embedder(settings)
        assert isinstance(embedder, CohereDenseEmbedder)

    def test_ollama_provider(self) -> None:
        settings = Settings(embedding_provider="ollama", embedding_model="nomic-embed-text")
        embedder = create_dense_embedder(settings)
        assert isinstance(embedder, OllamaDenseEmbedder)

    def test_openai_compatible_requires_base(self) -> None:
        settings = Settings(embedding_provider="openai_compatible", openai_api_key="key")
        with pytest.raises(EmbeddingError, match="EMBEDDING_API_BASE"):
            create_dense_embedder(settings)

    def test_openai_compatible_with_base(self) -> None:
        settings = Settings(
            embedding_provider="openai_compatible",
            openai_api_key="key",
            embedding_api_base="http://localhost:8000/v1",
        )
        embedder = create_dense_embedder(settings)
        assert isinstance(embedder, OpenAICompatibleDenseEmbedder)

    def test_invalid_provider_raises(self) -> None:
        settings = Settings(embedding_provider="unknown")
        with pytest.raises(ConfigurationError):
            create_dense_embedder(settings)


class TestCreateChatLLM:
    def test_mock_provider(self) -> None:
        llm = create_chat_llm(Settings(llm_provider="mock"))
        assert isinstance(llm, MockChatLLM)

    def test_anthropic_provider(self) -> None:
        llm = create_chat_llm(
            Settings(llm_provider="anthropic", anthropic_api_key="key"),
        )
        assert isinstance(llm, AnthropicChatLLM)

    def test_openai_provider(self) -> None:
        llm = create_chat_llm(Settings(llm_provider="openai", openai_api_key="key"))
        assert isinstance(llm, OpenAIChatLLM)

    def test_ollama_provider(self) -> None:
        llm = create_chat_llm(Settings(llm_provider="ollama"))
        assert isinstance(llm, OllamaChatLLM)

    def test_openai_compatible_requires_base(self) -> None:
        settings = Settings(llm_provider="openai_compatible", openai_api_key="key")
        with pytest.raises(ConfigurationError, match="LLM_API_BASE"):
            create_chat_llm(settings)


class TestLLMQueryExpander:
    def test_uses_injected_llm(self) -> None:
        mock_llm = MagicMock()
        mock_llm.complete.return_value = '["token", "jwt"]'
        expander = LLMQueryExpander(mock_llm)
        terms = expander.expand("auth")
        assert terms[0] == "auth"
        assert "token" in terms
