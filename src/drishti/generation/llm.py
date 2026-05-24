"""LLM clients for RAG generation (US-07.02, US-07.03)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any, Protocol

from drishti.exceptions import GenerationError

logger = logging.getLogger(__name__)


class ChatLLM(Protocol):
    """Chat completion interface with optional streaming."""

    @property
    def model(self) -> str:
        """Return the model identifier in use."""

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        """Return a full completion string."""

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> Iterator[str]:
        """Yield incremental text tokens."""


class AnthropicChatLLM:
    """Anthropic Messages API client with streaming support."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client: Any | None = None,
    ) -> None:
        if client is None and not api_key.strip():
            msg = "ANTHROPIC_API_KEY is required for generation"
            raise GenerationError(msg)
        self._model = model
        if client is not None:
            self._client: Any = client
        else:
            import anthropic

            self._client = anthropic.Anthropic(api_key=api_key)

    @property
    def model(self) -> str:
        return self._model

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        return "".join(
            self.stream(
                prompt,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
            ),
        )

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> Iterator[str]:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        try:
            with self._client.messages.stream(**kwargs) as stream:
                yield from stream.text_stream
        except Exception as exc:
            msg = "Anthropic generation request failed"
            raise GenerationError(msg) from exc


class OpenAIChatLLM:
    """OpenAI Chat Completions API client with streaming support."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client: Any | None = None,
    ) -> None:
        if client is None and not api_key.strip():
            msg = "OPENAI_API_KEY is required for generation"
            raise GenerationError(msg)
        self._model = model
        if client is not None:
            self._client: Any = client
        else:
            from openai import OpenAI

            self._client = OpenAI(api_key=api_key)

    @property
    def model(self) -> str:
        return self._model

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        return "".join(
            self.stream(
                prompt,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
            ),
        )

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> Iterator[str]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            msg = "OpenAI generation request failed"
            raise GenerationError(msg) from exc


class MockChatLLM:
    """Deterministic LLM for unit tests."""

    def __init__(self, *, model: str = "mock", response: str = "") -> None:
        self._model = model
        self._response = response or "Answer with citation [src/auth.py:L1-5]."

    @property
    def model(self) -> str:
        return self._model

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        return self._response

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> Iterator[str]:
        yield self._response
