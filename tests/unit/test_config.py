"""Unit tests for application settings."""

from __future__ import annotations

import pytest

from drishti.config import Settings, get_settings

pytestmark = pytest.mark.unit


class TestSettings:
    def test_qdrant_url_property(self) -> None:
        settings = Settings(qdrant_host="qdrant", qdrant_port=6333)
        assert settings.qdrant_url == "http://qdrant:6333"

    def test_api_auth_disabled_without_token(self) -> None:
        settings = Settings(api_token="")
        assert settings.api_auth_enabled is False

    def test_api_auth_enabled_with_token(self) -> None:
        settings = Settings(api_token="secret-token")
        assert settings.api_auth_enabled is True

    def test_parse_cors_origins_from_string(self) -> None:
        settings = Settings(cors_origins="http://a.test,http://b.test")
        assert settings.cors_origins == ["http://a.test", "http://b.test"]

    def test_collection_name_default(self) -> None:
        settings = Settings()
        assert settings.qdrant_collection_name == "drishti_chunks"

    def test_default_embedding_provider_is_openai(self) -> None:
        settings = Settings()
        assert settings.embedding_provider == "openai"

    def test_default_llm_provider_is_anthropic(self) -> None:
        settings = Settings()
        assert settings.llm_provider == "anthropic"

    def test_legacy_openai_embedding_model_fallback(self) -> None:
        settings = Settings(openai_embedding_model="text-embedding-3-large")
        assert settings.resolved_embedding_model() == "text-embedding-3-large"

    def test_get_settings_is_cached(self) -> None:
        get_settings.cache_clear()
        first = get_settings()
        second = get_settings()
        assert first is second
        get_settings.cache_clear()
