"""Shared retrieve / generate steps for the LangGraph agent."""

from __future__ import annotations

from drishti.agent.state import AgentState
from drishti.generation.citations import (
    filter_valid_citations,
    parse_citations,
    validate_citations,
)
from drishti.generation.llm import ChatLLM
from drishti.generation.pipeline import RAGPipeline
from drishti.generation.prompts import RAG_SYSTEM_PROMPT


def retrieve_context(rag: RAGPipeline, state: AgentState) -> AgentState:
    """Hybrid search + prompt build; may loop when context is empty."""
    question = state["question"]
    chunks, user_prompt = rag.prepare_context(
        question,
        filters=state.get("filters"),
        conversation_history=None,
        workspace_memory=state.get("workspace_memory", ""),
    )
    passes = state.get("retrieval_pass", 0) + 1
    max_passes = state.get("max_passes", 2)
    return {
        "context_chunks": chunks,
        "user_prompt": user_prompt,
        "retrieval_pass": passes,
        "needs_retry": len(chunks) == 0 and passes < max_passes,
    }


def generate_answer(
    rag: RAGPipeline,
    llm: ChatLLM,
    state: AgentState,
    *,
    answer: str | None = None,
) -> AgentState:
    """LLM completion + citation validation; may trigger re-retrieval."""
    text = answer
    if text is None:
        text = llm.complete(
            state["user_prompt"],
            system=RAG_SYSTEM_PROMPT,
            max_tokens=rag.settings.llm_max_tokens,
            temperature=rag.settings.llm_temperature,
        )
    chunks = state.get("context_chunks") or ()
    parsed = parse_citations(text)
    validated = validate_citations(parsed, chunks)
    citations = filter_valid_citations(validated)
    low_confidence = len(chunks) < 2 and "[src:" not in text
    passes = state.get("retrieval_pass", 1)
    max_passes = state.get("max_passes", 2)
    return {
        "answer": text,
        "citations": citations,
        "needs_retry": low_confidence and passes < max_passes,
    }
