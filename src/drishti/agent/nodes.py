"""Shared retrieve / generate steps for the LangGraph agent."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from langgraph.config import get_stream_writer

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

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

logger = get_logger(__name__)

_TOOL_CALL_PROMPT = """You may call at most one tool before search runs.

Available tools (name — description):
{tool_lines}

User question: {question}

Reply with a single JSON object only:
{{"tool": "<name>", "arguments": {{...}}}}
or {{"tool": null}} if no tool is needed.
"""


def invoke_agent_tools(tools: list[BaseTool], llm: ChatLLM, state: AgentState) -> AgentState:
    """LLM-select at most one LangChain tool and append its output to workspace memory."""
    if state.get("tools_invoked") or not tools:
        return {"tools_invoked": True}

    by_name = {tool.name: tool for tool in tools}
    tool_lines = "\n".join(f"- {tool.name}: {tool.description or ''}" for tool in tools)
    prompt = _TOOL_CALL_PROMPT.format(
        tool_lines=tool_lines,
        question=state.get("question", "").strip(),
    )
    raw = llm.complete(
        prompt,
        system="You are a tool router. Output JSON only.",
        max_tokens=512,
    )
    selection = _parse_tool_call_json(raw)
    if selection is None:
        return {"tools_invoked": True}

    tool_name = str(selection.get("tool", "")).strip()
    tool = by_name.get(tool_name)
    if tool is None:
        return {"tools_invoked": True}

    arguments = selection.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}

    try:
        output = tool.invoke(arguments)
    except Exception as exc:
        output = json.dumps({"error": str(exc)}, ensure_ascii=False)
    else:
        if not isinstance(output, str):
            output = json.dumps(output, ensure_ascii=False, default=str)

    prior = state.get("workspace_memory", "")
    appendix = f"\n\n[Tool {tool_name} result]\n{output}"
    logger.info("agent_tool_invoked", tool=tool_name)
    return {
        "tools_invoked": True,
        "workspace_memory": f"{prior}{appendix}".strip(),
    }


def _parse_tool_call_json(text: str) -> dict[str, object] | None:
    stripped = text.strip()
    if not stripped:
        return None
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    if parsed.get("tool") is None:
        return None
    return parsed


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
        if state.get("stream_tokens"):
            writer = get_stream_writer()
            parts: list[str] = []
            for token in llm.stream(
                state["user_prompt"],
                system=RAG_SYSTEM_PROMPT,
                max_tokens=rag.settings.llm_max_tokens,
                temperature=rag.settings.llm_temperature,
            ):
                writer({"event": "token", "text": token})
                parts.append(token)
            text = "".join(parts)
        else:
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
