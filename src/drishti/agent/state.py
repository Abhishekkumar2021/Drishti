"""Agent graph state definitions."""

from __future__ import annotations

from typing import TypedDict

from drishti.generation.models import Citation, ContextChunk


class AgentState(TypedDict, total=False):
    """State passed between LangGraph nodes."""

    question: str
    filters: dict[str, str] | None
    workspace_memory: str
    conversation_prefix: str
    context_chunks: tuple[ContextChunk, ...]
    user_prompt: str
    answer: str
    citations: list[Citation]
    retrieval_pass: int
    max_passes: int
    needs_retry: bool
