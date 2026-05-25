"""Unit tests for generation LLM clients."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from drishti.config import Settings
from drishti.generation.factory import create_chat_llm
from drishti.generation.llm import AnthropicChatLLM, MockChatLLM, OpenAIChatLLM

pytestmark = pytest.mark.unit


class TestCreateChatLLM:
    def test_anthropic_when_key_present(self) -> None:
        llm = create_chat_llm(
            Settings(anthropic_api_key="key", llm_provider="anthropic"),
        )
        assert isinstance(llm, AnthropicChatLLM)

    def test_openai_client(self) -> None:
        llm = OpenAIChatLLM(api_key="key", model="gpt-4o-mini")
        assert isinstance(llm, OpenAIChatLLM)

    def test_mock_client(self) -> None:
        llm = MockChatLLM()
        text = llm.complete("q")
        assert "LLM_PROVIDER=mock" in text


class TestAnthropicStream:
    def test_streams_text(self) -> None:
        mock_client = MagicMock()
        mock_stream = MagicMock()
        mock_stream.text_stream = ["Hello", " world"]
        mock_client.messages.stream.return_value.__enter__.return_value = mock_stream

        llm = AnthropicChatLLM(api_key="key", model="claude", client=mock_client)
        tokens = list(llm.stream("prompt", system="sys"))

        assert tokens == ["Hello", " world"]
