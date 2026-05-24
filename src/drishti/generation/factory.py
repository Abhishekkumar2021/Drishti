"""Factory for chat LLM clients."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drishti.exceptions import ConfigurationError, GenerationError
from drishti.generation.llm import AnthropicChatLLM, ChatLLM, MockChatLLM, OpenAIChatLLM

if TYPE_CHECKING:
    from drishti.config import Settings


def create_chat_llm(settings: Settings, *, provider: str | None = None) -> ChatLLM:
    """Instantiate a chat LLM from application settings."""
    resolved = (provider or getattr(settings, "llm_provider", None) or "anthropic").strip().lower()

    if resolved == "mock":
        return MockChatLLM()

    if resolved == "anthropic":
        api_key = settings.anthropic_api_key.strip()
        if not api_key:
            msg = "ANTHROPIC_API_KEY is required for LLM generation"
            raise GenerationError(msg)
        return AnthropicChatLLM(api_key=api_key, model=settings.anthropic_model)

    if resolved == "openai":
        api_key = settings.openai_api_key.strip()
        if not api_key:
            msg = "OPENAI_API_KEY is required for LLM generation"
            raise GenerationError(msg)
        model = getattr(settings, "llm_model", "") or "gpt-4o-mini"
        return OpenAIChatLLM(api_key=api_key, model=model.strip() or "gpt-4o-mini")

    msg = f"Unsupported LLM provider for generation: {resolved!r}"
    raise ConfigurationError(msg)
