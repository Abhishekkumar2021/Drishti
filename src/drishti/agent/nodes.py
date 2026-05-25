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
from drishti.observability.logging import get_logger
from drishti.search.expansion import LLMQueryExpander, combine_expanded_query

logger = get_logger(__name__)


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
    needs_retry = len(chunks) == 0 and passes < max_passes
    return {
        "context_chunks": chunks,
        "user_prompt": user_prompt,
        "retrieval_pass": passes,
        "needs_retry": needs_retry,
        "retry_mode": "empty" if needs_retry else "",
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
    needs_retry = low_confidence and passes < max_passes
    if needs_retry:
        logger.info(
            "agent_grade_retry",
            retrieval_pass=passes,
            retry_mode="low_confidence",
            chunk_count=len(chunks),
        )
    return {
        "answer": text,
        "citations": citations,
        "needs_retry": needs_retry,
        "retry_mode": "low_confidence" if needs_retry else "",
    }


def expand_query(llm: ChatLLM, state: AgentState) -> AgentState:
    """Rewrite the question with LLM query expansion before another retrieval pass."""
    question = state.get("question", "").strip()
    expander = LLMQueryExpander(llm)
    terms = expander.expand(question)
    expanded = combine_expanded_query(terms)
    logger.info(
        "agent_query_expanded",
        retrieval_pass=state.get("retrieval_pass", 0),
        term_count=len(terms),
    )
    return {
        "question": expanded,
        "query_expanded": True,
        "needs_retry": False,
        "retry_mode": "",
    }
