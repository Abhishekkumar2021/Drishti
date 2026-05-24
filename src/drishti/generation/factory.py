"""Factory for chat LLM clients."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drishti.exceptions import ConfigurationError
from drishti.generation.llm import (
    AnthropicChatLLM,
    ChatLLM,
    MockChatLLM,
    OllamaChatLLM,
    OpenAIChatLLM,
)

if TYPE_CHECKING:
    from drishti.config import Settings


def create_chat_llm(settings: Settings, *, provider: str | None = None) -> ChatLLM:
    """Instantiate a chat LLM from ``LLM_PROVIDER`` and related settings."""
    try:
        settings.validate_llm_provider()
    except ValueError as exc:
        raise ConfigurationError(str(exc)) from exc

    resolved = (provider or settings.llm_provider).strip().lower()
    model = settings.resolved_llm_model()

    if resolved == "mock":
        return MockChatLLM(model=model)

    if resolved == "anthropic":
        return AnthropicChatLLM(
            api_key=settings.api_key_for_llm_provider(),
            model=model,
        )

    if resolved in {"openai", "openai_compatible"}:
        api_base = settings.resolved_llm_api_base()
        if resolved == "openai_compatible" and not api_base:
            msg = "LLM_API_BASE is required when LLM_PROVIDER=openai_compatible"
            raise ConfigurationError(msg)
        return OpenAIChatLLM(
            api_key=settings.api_key_for_llm_provider(),
            model=model,
            api_base=api_base,
        )

    if resolved == "ollama":
        return OllamaChatLLM(
            model=model,
            api_base=settings.resolved_llm_api_base(),
        )

    msg = f"Unsupported LLM provider: {resolved}"
    raise ConfigurationError(msg)
