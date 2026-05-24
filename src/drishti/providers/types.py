"""Supported third-party model provider identifiers."""

from __future__ import annotations

from typing import Literal

EmbeddingProvider = Literal[
    "openai",
    "cohere",
    "ollama",
    "openai_compatible",
    "hashing",
]

LLMProvider = Literal[
    "anthropic",
    "openai",
    "ollama",
    "openai_compatible",
    "mock",
]

RerankProvider = Literal[
    "auto",
    "cohere",
    "lexical",
]

EMBEDDING_PROVIDERS: frozenset[str] = frozenset(
    {"openai", "cohere", "ollama", "openai_compatible", "hashing"},
)
LLM_PROVIDERS: frozenset[str] = frozenset(
    {"anthropic", "openai", "ollama", "openai_compatible", "mock"},
)
RERANK_PROVIDERS: frozenset[str] = frozenset({"auto", "cohere", "lexical"})
