"""Drishti configuration management.

All application settings are loaded from environment variables
with sensible defaults for local development.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ─── Qdrant Vector Database ──────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "drishti_codebase"

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

    # ─── Neo4j (Phase 4) ─────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "drishtidev"

    # ─── Application ─────────────────────────────
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ─── Search Defaults ─────────────────────────
    search_top_k: int = 10
    rrf_k: int = 60
    max_context_chunks: int = 15

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
