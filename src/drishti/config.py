"""Drishti configuration management.

All application settings are loaded from environment variables
with sensible defaults for local development.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from drishti.providers.types import EMBEDDING_PROVIDERS, LLM_PROVIDERS, RERANK_PROVIDERS


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Qdrant Vector Database ──────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "drishti_chunks"

    # ─── Embedding (provider-agnostic) ───────────
    embedding_provider: str = "openai"
    embedding_model: str = ""
    embedding_dimensions: int = 0
    embedding_api_base: str = ""
    embedding_api_key: str = ""

    # ─── LLM (provider-agnostic) ───────────────
    llm_provider: str = "anthropic"
    llm_model: str = ""
    llm_api_base: str = ""
    llm_api_key: str = ""

    # ─── Re-ranking ──────────────────────────────
    rerank_provider: str = "auto"
    rerank_model: str = ""

    # ─── Provider API keys (shared + env fallbacks) ─
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-v3.5"

    # ─── PostgreSQL (system of record) ───────────
    database_url: str = ""
    database_pool_size: int = 5

    # ─── MinIO (artifact object storage) ─────────
    enable_minio: bool = False
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "drishti"
    minio_secret_key: str = "drishtidev"
    minio_bucket: str = "drishti-artifacts"
    minio_secure: bool = False
    minio_region: str = ""

    # ─── Agent (LangGraph retrieve → generate) ───
    agent_max_retrieval_loops: int = 2

    # ─── Background workers (Arq) ────────────────
    worker_enabled: bool = False

    # ─── Observability ───────────────────────────
    structured_logging: bool = True
    log_json: bool = True
    otel_enabled: bool = False
    otel_service_name: str = "drishti-api"

    # ─── Redis (Cache & Rate Limiting) ───────────
    redis_url: str = "redis://localhost:6379/0"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    conversation_ttl_seconds: int = 604_800
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60

    # ─── Neo4j (Phase 4, optional) ───────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_enabled: bool = False

    # ─── Application ─────────────────────────────
    debug: bool = False
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_token: str = ""
    expose_openapi_docs: bool = True
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
    )
    health_check_timeout_seconds: float = 5.0
    ingestion_allowed_roots: list[str] = Field(default_factory=list)
    max_upload_bytes: int = 52_428_800
    workspaces_cache_root: str = ""

    # ─── Search Defaults ─────────────────────────
    search_top_k: int = 10
    search_retrieval_limit: int = 50
    rrf_k: int = 60
    rerank_min_score: float = 0.0
    max_context_chunks: int = 15

    # ─── RAG / Generation ────────────────────────
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    rag_max_context_chars: int = 120_000

    @field_validator(
        "embedding_provider",
        "llm_provider",
        "rerank_provider",
        mode="before",
    )
    @classmethod
    def normalize_provider_name(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    @field_validator("cors_origins", "ingestion_allowed_roots", mode="before")
    @classmethod
    def parse_comma_separated_list(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    @property
    def postgres_enabled(self) -> bool:
        """Whether PostgreSQL is configured as the system of record."""
        return bool(self.database_url.strip())

    @property
    def minio_enabled(self) -> bool:
        """Whether MinIO object storage is active."""
        return self.enable_minio and bool(
            self.minio_endpoint.strip() and self.minio_access_key.strip(),
        )

    @property
    def qdrant_url(self) -> str:
        """HTTP URL for the Qdrant REST API."""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    @property
    def api_auth_enabled(self) -> bool:
        """Whether Bearer token authentication is required."""
        return bool(self.api_token.strip())

    @property
    def enable_openapi_docs(self) -> bool:
        """Whether Swagger UI and ReDoc are exposed."""
        return self.debug or self.expose_openapi_docs

    def ingestion_root_allowlist(self) -> list[str]:
        """Return configured ingestion path allowlist (may be empty)."""
        return self.ingestion_allowed_roots

    def resolved_embedding_model(self) -> str:
        """Return the configured embedding model (explicit or provider default)."""
        explicit = self.embedding_model.strip()
        if explicit:
            return explicit
        if self.embedding_provider == "cohere":
            return "embed-english-v3.0"
        if self.embedding_provider == "ollama":
            return "nomic-embed-text"
        return self.openai_embedding_model

    def resolved_embedding_dimensions(self) -> int:
        """Return vector dimensionality for the active embedding model."""
        if self.embedding_dimensions > 0:
            return self.embedding_dimensions
        return self.openai_embedding_dimensions

    def resolved_llm_model(self) -> str:
        """Return the configured chat model (explicit or provider default)."""
        explicit = self.llm_model.strip()
        if explicit:
            return explicit
        if self.llm_provider == "openai":
            return "gpt-4o-mini"
        if self.llm_provider == "ollama":
            return "llama3.2"
        return self.anthropic_model

    def resolved_rerank_model(self) -> str:
        """Return the configured rerank model name."""
        explicit = self.rerank_model.strip()
        if explicit:
            return explicit
        return self.cohere_rerank_model

    def resolved_embedding_api_base(self) -> str:
        """Return API base URL for embedding HTTP backends."""
        explicit = self.embedding_api_base.strip()
        if explicit:
            return explicit.rstrip("/")
        if self.embedding_provider == "ollama":
            return "http://localhost:11434"
        return ""

    def resolved_llm_api_base(self) -> str:
        """Return API base URL for chat LLM HTTP backends."""
        explicit = self.llm_api_base.strip()
        if explicit:
            return explicit.rstrip("/")
        if self.llm_provider == "ollama":
            return "http://localhost:11434"
        return ""

    def api_key_for_embedding_provider(self) -> str:
        """Resolve API key for the active embedding provider."""
        override = self.embedding_api_key.strip()
        if override:
            return override
        provider = self.embedding_provider
        if provider in {"openai", "openai_compatible"}:
            return self.openai_api_key.strip()
        if provider == "cohere":
            return self.cohere_api_key.strip()
        return ""

    def api_key_for_llm_provider(self) -> str:
        """Resolve API key for the active LLM provider."""
        override = self.llm_api_key.strip()
        if override:
            return override
        provider = self.llm_provider
        if provider == "anthropic":
            return self.anthropic_api_key.strip()
        if provider in {"openai", "openai_compatible"}:
            return self.openai_api_key.strip()
        return ""

    def api_key_for_rerank_provider(self) -> str:
        """Resolve API key for Cohere reranking."""
        return self.cohere_api_key.strip()

    def validate_embedding_provider(self) -> None:
        """Raise if ``embedding_provider`` is not supported."""
        if self.embedding_provider not in EMBEDDING_PROVIDERS:
            msg = (
                f"Unsupported EMBEDDING_PROVIDER={self.embedding_provider!r}. "
                f"Choose one of: {', '.join(sorted(EMBEDDING_PROVIDERS))}"
            )
            raise ValueError(msg)

    def validate_llm_provider(self) -> None:
        """Raise if ``llm_provider`` is not supported."""
        if self.llm_provider not in LLM_PROVIDERS:
            msg = (
                f"Unsupported LLM_PROVIDER={self.llm_provider!r}. "
                f"Choose one of: {', '.join(sorted(LLM_PROVIDERS))}"
            )
            raise ValueError(msg)

    def validate_rerank_provider(self) -> None:
        """Raise if ``rerank_provider`` is not supported."""
        if self.rerank_provider not in RERANK_PROVIDERS:
            msg = (
                f"Unsupported RERANK_PROVIDER={self.rerank_provider!r}. "
                f"Choose one of: {', '.join(sorted(RERANK_PROVIDERS))}"
            )
            raise ValueError(msg)

    def validate_runtime_configuration(self, *, strict: bool | None = None) -> None:
        """Validate provider names and required credentials for the active environment.

        Args:
            strict: When True, require API keys for cloud providers. Defaults to
                ``not debug`` (production-like environments require keys).
        """
        from drishti.exceptions import ConfigurationError

        require_keys = not self.debug if strict is None else strict

        self.validate_embedding_provider()
        self.validate_llm_provider()
        self.validate_rerank_provider()

        if self.resolved_embedding_dimensions() <= 0:
            msg = "EMBEDDING_DIMENSIONS (or OPENAI_EMBEDDING_DIMENSIONS) must be positive"
            raise ConfigurationError(msg)

        if (
            self.embedding_provider == "openai_compatible"
            and not self.resolved_embedding_api_base()
        ):
            msg = "EMBEDDING_API_BASE is required when EMBEDDING_PROVIDER=openai_compatible"
            raise ConfigurationError(msg)

        if self.llm_provider == "openai_compatible" and not self.resolved_llm_api_base():
            msg = "LLM_API_BASE is required when LLM_PROVIDER=openai_compatible"
            raise ConfigurationError(msg)

        if (
            require_keys
            and self.embedding_provider not in {"hashing", "ollama"}
            and not self.api_key_for_embedding_provider()
        ):
            msg = (
                f"API key required for EMBEDDING_PROVIDER={self.embedding_provider!r} "
                "(set EMBEDDING_API_KEY or the provider-specific key)"
            )
            raise ConfigurationError(msg)

        if (
            require_keys
            and self.llm_provider not in {"mock", "ollama"}
            and not self.api_key_for_llm_provider()
        ):
            msg = (
                f"API key required for LLM_PROVIDER={self.llm_provider!r} "
                "(set LLM_API_KEY or the provider-specific key)"
            )
            raise ConfigurationError(msg)

        if (
            require_keys
            and self.rerank_provider == "cohere"
            and not self.api_key_for_rerank_provider()
        ):
            msg = "COHERE_API_KEY is required when RERANK_PROVIDER=cohere"
            raise ConfigurationError(msg)

    def runtime_provider_summary(self) -> dict[str, str]:
        """Return non-secret provider configuration for logging and health."""
        return {
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.resolved_embedding_model(),
            "embedding_dimensions": str(self.resolved_embedding_dimensions()),
            "llm_provider": self.llm_provider,
            "llm_model": self.resolved_llm_model(),
            "rerank_provider": self.rerank_provider,
            "rerank_model": self.resolved_rerank_model(),
            "postgres_enabled": str(self.postgres_enabled),
            "minio_enabled": str(self.minio_enabled),
            "worker_enabled": str(self.worker_enabled),
        }


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    settings = Settings()
    settings.validate_runtime_configuration(strict=False)
    return settings
