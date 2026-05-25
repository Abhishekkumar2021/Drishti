"""RAG context preparation: hybrid search → chunks → LLM prompt."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drishti.api.schemas import ChatMessage
from drishti.generation.citations import (
    filter_valid_citations,
    parse_citations,
    validate_citations,
)
from drishti.generation.context import ContextBuilder
from drishti.generation.llm import ChatLLM
from drishti.generation.models import Citation, ContextChunk
from drishti.generation.prompts import build_user_prompt
from drishti.search.pipeline import HybridSearchPipeline

if TYPE_CHECKING:
    from drishti.config import Settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Retrieval and context assembly for the LangGraph agent."""

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

    @property
    def settings(self) -> Settings:
        """Active application settings."""
        return self._settings

    @property
    def llm(self) -> ChatLLM:
        """Chat model used by the agent generate step."""
        return self._llm

    @property
    def search(self) -> HybridSearchPipeline:
        """Hybrid search pipeline backing retrieval."""
        return self._search

    def prepare_context(
        self,
        question: str,
        *,
        filters: dict[str, str] | None,
        conversation_history: list[ChatMessage] | None,
        workspace_memory: str = "",
    ) -> tuple[tuple[ContextChunk, ...], str]:
        """Run hybrid search and build the user prompt for the LLM."""
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

    def extract_citations(
        self,
        answer: str,
        chunks: tuple[ContextChunk, ...],
    ) -> list[Citation]:
        """Parse and validate citation tags against retrieved chunks."""
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
