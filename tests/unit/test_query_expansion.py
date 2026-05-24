"""Unit tests for query expansion (US-06.05)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from drishti.config import Settings
from drishti.exceptions import SearchError
from drishti.search.expansion import (
    AnthropicQueryExpander,
    PassthroughQueryExpander,
    StaticQueryExpander,
    combine_expanded_query,
)

pytestmark = pytest.mark.unit


class TestPassthroughQueryExpander:
    def test_returns_original_query(self) -> None:
        assert PassthroughQueryExpander().expand("auth token") == ["auth token"]


class TestStaticQueryExpander:
    def test_adds_configured_synonyms(self) -> None:
        expander = StaticQueryExpander({"auth": ["token", "jwt", "bearer"]})
        terms = expander.expand("auth")
        assert "auth" in terms
        assert "token" in terms
        assert "jwt" in terms


class TestAnthropicQueryExpander:
    def test_parses_json_synonyms(self) -> None:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(text='["JWT", "bearer", "authenticate"]')]
        )
        settings = Settings(anthropic_api_key="test-key")
        expander = AnthropicQueryExpander(settings, client=mock_client)

        terms = expander.expand("auth")

        assert terms[0] == "auth"
        assert "JWT" in terms

    def test_requires_api_key_when_client_not_injected(self) -> None:
        settings = Settings(anthropic_api_key="")
        with pytest.raises(SearchError, match="ANTHROPIC_API_KEY"):
            AnthropicQueryExpander(settings)


class TestCombineExpandedQuery:
    def test_joins_unique_terms(self) -> None:
        assert combine_expanded_query(["auth", "token", "jwt"]) == "auth token jwt"
