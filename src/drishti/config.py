"""Drishti configuration management.

All application settings are loaded from environment variables
with sensible defaults for local development.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # ─── OpenAI (Embeddings) ─────────────────────
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # ─── Anthropic (LLM Generation) ──────────────
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # ─── Cohere (Re-ranking) ─────────────────────
    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-v3.5"

    # ─── Redis (Cache) ───────────────────────────
    redis_url: str = "redis://localhost:6379/0"

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


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
