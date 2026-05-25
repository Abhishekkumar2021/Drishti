"""LangGraph agent — sole entry point for grounded Q&A."""

from __future__ import annotations

import time
from collections.abc import Iterator

from drishti.agent.graph import build_rag_graph
from drishti.agent.nodes import generate_answer, retrieve_context
from drishti.agent.state import AgentState
from drishti.api.schemas import ChatMessage
from drishti.config import Settings
from drishti.generation.models import RAGAnswer, StreamEvent
from drishti.generation.pipeline import RAGPipeline
from drishti.generation.prompts import RAG_SYSTEM_PROMPT
from drishti.generation.streaming import (
    citation_event,
    context_event,
    done_event,
    token_event,
)


class AgentRunner:
    """Retrieve → grade → generate agent (LangGraph)."""

    def __init__(self, rag: RAGPipeline, settings: Settings) -> None:
        self._rag = rag
        self._settings = settings
        self._graph = build_rag_graph(rag, rag.llm).compile()

    def ask(
        self,
        question: str,
        *,
        filters: dict[str, str] | None = None,
        conversation_history: list[ChatMessage] | None = None,
        workspace_memory: str = "",
    ) -> RAGAnswer:
        final = self._graph.invoke(
            self._initial_state(
                question,
                filters=filters,
                conversation_history=conversation_history,
                workspace_memory=workspace_memory,
            ),
        )
        chunks = final.get("context_chunks") or ()
        return RAGAnswer(
            question=question.strip(),
            answer=str(final.get("answer", "")),
            citations=tuple(final.get("citations") or []),
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
        """Stream tokens using the same retrieve → generate → grade loop as the graph."""
        started = time.perf_counter()
        state = self._initial_state(
            question,
            filters=filters,
            conversation_history=conversation_history,
            workspace_memory=workspace_memory,
        )
        token_count = 0

        while True:
            state = {**state, **retrieve_context(self._rag, state)}
            if state.get("needs_retry"):
                continue

            chunks = state.get("context_chunks") or ()
            user_prompt = state.get("user_prompt", "")
            yield context_event(chunks)

            answer_parts: list[str] = []
            for token in self._rag.llm.stream(
                user_prompt,
                system=RAG_SYSTEM_PROMPT,
                max_tokens=self._settings.llm_max_tokens,
                temperature=self._settings.llm_temperature,
            ):
                token_count += 1
                answer_parts.append(token)
                yield token_event(token)

            state = {
                **state,
                **generate_answer(
                    self._rag,
                    self._rag.llm,
                    state,
                    answer="".join(answer_parts),
                ),
            }
            for citation in state.get("citations") or []:
                yield citation_event(citation)

            if not state.get("needs_retry"):
                break

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        yield done_event(total_tokens=token_count, execution_time_ms=elapsed_ms)

    def _initial_state(
        self,
        question: str,
        *,
        filters: dict[str, str] | None,
        conversation_history: list[ChatMessage] | None,
        workspace_memory: str,
    ) -> AgentState:
        return {
            "question": question,
            "filters": filters,
            "workspace_memory": _history_prefix(conversation_history, workspace_memory),
            "max_passes": self._settings.agent_max_retrieval_loops,
            "retrieval_pass": 0,
        }


def _history_prefix(
    messages: list[ChatMessage] | None,
    workspace_memory: str,
) -> str:
    parts: list[str] = []
    if workspace_memory.strip():
        parts.append(workspace_memory.strip())
    if messages:
        lines = []
        for message in messages[-12:]:
            lines.append(f"{message.role}: {message.content}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)
