"""RAG pipeline orchestrating search, context, and generation."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import TYPE_CHECKING

from drishti.api.schemas import ChatMessage
from drishti.generation.citations import (
    filter_valid_citations,
    parse_citations,
    validate_citations,
)
from drishti.generation.context import ContextBuilder
from drishti.generation.llm import ChatLLM
from drishti.generation.models import Citation, ContextChunk, RAGAnswer, StreamEvent
from drishti.generation.prompts import RAG_SYSTEM_PROMPT, build_user_prompt
from drishti.generation.streaming import (
    citation_event,
    context_event,
    done_event,
    token_event,
)
from drishti.search.pipeline import HybridSearchPipeline

if TYPE_CHECKING:
    from drishti.config import Settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """End-to-end RAG: retrieve context, prompt LLM, parse citations."""

    def __init__(
        self,
        *,
        search: HybridSearchPipeline,
        llm: ChatLLM,
        context_builder: ContextBuilder,
        settings: Settings,
    ) -> None:
        self._search = search
        self._llm = llm
        self._context_builder = context_builder
        self._settings = settings

    def ask(
        self,
        question: str,
        *,
        filters: dict[str, str] | None = None,
        conversation_history: list[ChatMessage] | None = None,
        workspace_memory: str = "",
    ) -> RAGAnswer:
        """Run non-streaming RAG and return the full answer."""
        chunks, user_prompt = self._prepare_context(
            question,
            filters=filters,
            conversation_history=conversation_history,
            workspace_memory=workspace_memory,
        )
        answer = self._llm.complete(
            user_prompt,
            system=RAG_SYSTEM_PROMPT,
            max_tokens=self._settings.llm_max_tokens,
            temperature=self._settings.llm_temperature,
        )
        citations = self._extract_citations(answer, chunks)
        return RAGAnswer(
            question=question.strip(),
            answer=answer,
            citations=tuple(citations),
            context_chunks=chunks,
        )

    def ask_stream(
        self,
        question: str,
        *,
        filters: dict[str, str] | None = None,
        conversation_history: list[ChatMessage] | None = None,
        workspace_memory: str = "",
    ) -> Iterator[StreamEvent]:
        """Yield SSE-ready stream events for a RAG answer."""
        started = time.perf_counter()
        chunks, user_prompt = self._prepare_context(
            question,
            filters=filters,
            conversation_history=conversation_history,
            workspace_memory=workspace_memory,
        )
        yield context_event(chunks)

        token_count = 0
        answer_parts: list[str] = []
        for token in self._llm.stream(
            user_prompt,
            system=RAG_SYSTEM_PROMPT,
            max_tokens=self._settings.llm_max_tokens,
            temperature=self._settings.llm_temperature,
        ):
            token_count += 1
            answer_parts.append(token)
            yield token_event(token)

        answer = "".join(answer_parts)
        for citation in self._extract_citations(answer, chunks):
            yield citation_event(citation)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        yield done_event(total_tokens=token_count, execution_time_ms=elapsed_ms)

    def _prepare_context(
        self,
        question: str,
        *,
        filters: dict[str, str] | None,
        conversation_history: list[ChatMessage] | None,
        workspace_memory: str = "",
    ) -> tuple[tuple[ContextChunk, ...], str]:
        hits = self._search.search(
            question,
            filters=filters,
            limit=self._settings.max_context_chunks,
        )
        chunks = self._context_builder.build_from_hits(hits)
        context_xml = self._context_builder.render_xml(chunks)
        history_prefix = _format_history(conversation_history, workspace_memory)
        user_prompt = build_user_prompt(
            question,
            context_xml,
            conversation_prefix=history_prefix,
        )
        return chunks, user_prompt

    def _extract_citations(
        self,
        answer: str,
        chunks: tuple[ContextChunk, ...],
    ) -> list[Citation]:
        parsed = parse_citations(answer)
        validated = validate_citations(parsed, chunks)
        return filter_valid_citations(validated)


def _format_history(
    messages: list[ChatMessage] | None,
    workspace_memory: str = "",
) -> str:
    parts: list[str] = []
    if workspace_memory.strip():
        parts.append(f"## Workspace memory\n{workspace_memory.strip()}")
    if messages:
        lines = ["## Conversation history"]
        for message in messages[-12:]:
            lines.append(f"{message.role}: {message.content}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)
