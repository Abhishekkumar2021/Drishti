"""Provider-agnostic chat LLM clients with streaming (US-07.02, US-07.03)."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any, Protocol

import httpx

from drishti.exceptions import GenerationError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 60.0


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
            msg = "API key is required for Anthropic LLM"
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
        api_base: str = "",
        client: Any | None = None,
    ) -> None:
        if client is None and not api_key.strip():
            msg = "API key is required for OpenAI LLM"
            raise GenerationError(msg)
        self._model = model
        if client is not None:
            self._client: Any = client
        else:
            from openai import OpenAI

            if api_base:
                self._client = OpenAI(api_key=api_key, base_url=api_base)
            else:
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


class OllamaChatLLM:
    """Ollama local chat API client."""

    def __init__(
        self,
        *,
        model: str,
        api_base: str,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        client: httpx.Client | None = None,
    ) -> None:
        self._model = model
        self._api_base = api_base.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout_seconds)

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
        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        if system:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        try:
            with self._client.stream(
                "POST",
                f"{self._api_base}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    message = data.get("message") or {}
                    content = message.get("content")
                    if content:
                        yield str(content)
        except Exception as exc:
            msg = "Ollama generation request failed"
            raise GenerationError(msg) from exc


class MockChatLLM:
    """Deterministic LLM stub for unit tests."""

    def __init__(
        self,
        *,
        model: str = "mock",
        response: str = "",
    ) -> None:
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
