"""LLM query expansion (US-06.05)."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Protocol

from drishti.generation.llm import ChatLLM

if TYPE_CHECKING:
    from drishti.config import Settings

logger = logging.getLogger(__name__)

_EXPANSION_PROMPT = """You are a software search utility. Expand the user query with \
alternative terminology.
Output a flat JSON list of strings containing:
1. Exact class or method names that map to the concept.
2. Common API terminology, variables, or exception names.

Query: {query}
Response:"""

_JSON_LIST_RE = re.compile(r"\[[\s\S]*\]")


class QueryExpander(Protocol):
    """Protocol for expanding user queries with related technical terms."""

    def expand(self, query: str) -> list[str]:
        """Return the original query plus synonym terms."""


class PassthroughQueryExpander:
    """No-op expander that returns only the original query."""

    def expand(self, query: str) -> list[str]:
        """Return the query unchanged as a single-element list."""
        stripped = query.strip()
        return [stripped] if stripped else []


class LLMQueryExpander:
    """Expand queries using any configured ``ChatLLM`` provider."""

    def __init__(self, llm: ChatLLM, *, max_terms: int = 12) -> None:
        """Wire a chat LLM client for synonym generation."""
        self._llm = llm
        self._max_terms = max(1, max_terms)

    def expand(self, query: str) -> list[str]:
        """Return deduplicated query terms including LLM-generated synonyms."""
        stripped = query.strip()
        if not stripped:
            return []

        raw_text = self._llm.complete(
            _EXPANSION_PROMPT.format(query=stripped),
            max_tokens=256,
        )
        extra_terms = _parse_json_term_list(raw_text)
        return _dedupe_terms([stripped, *extra_terms], max_terms=self._max_terms)


class AnthropicQueryExpander(LLMQueryExpander):
    """Backward-compatible expander that builds an Anthropic client from settings."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: object | None = None,
        max_terms: int = 12,
    ) -> None:
        from drishti.generation.llm import AnthropicChatLLM

        llm = AnthropicChatLLM(
            api_key=settings.api_key_for_llm_provider(),
            model=settings.resolved_llm_model(),
            client=client,
        )
        super().__init__(llm, max_terms=max_terms)


class StaticQueryExpander:
    """Test expander with predefined synonym map."""

    def __init__(self, synonyms: dict[str, list[str]]) -> None:
        """Map normalized query keys to extra search terms."""
        self._synonyms = {key.lower(): values for key, values in synonyms.items()}

    def expand(self, query: str) -> list[str]:
        """Return query plus configured synonyms when the key matches."""
        stripped = query.strip()
        if not stripped:
            return []
        extras = self._synonyms.get(stripped.lower(), [])
        return _dedupe_terms([stripped, *extras], max_terms=20)


def combine_expanded_query(terms: list[str]) -> str:
    """Join expanded terms into a single retrieval query string."""
    return " ".join(terms)


def _parse_json_term_list(text: str) -> list[str]:
    match = _JSON_LIST_RE.search(text)
    if not match:
        logger.warning("Query expansion response was not JSON; ignoring extras")
        return []
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        logger.warning("Failed to parse query expansion JSON")
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()]


def _dedupe_terms(terms: list[str], *, max_terms: int) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        normalized = term.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
        if len(unique) >= max_terms:
            break
    return unique
