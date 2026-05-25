"""LangGraph agent — sole entry point for grounded Q&A."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from drishti.agent.graph import build_rag_graph
from drishti.agent.state import AgentState
from drishti.agent.stream_mapping import initial_stream_state, iter_sse_from_graph_stream

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig
    from langchain_core.tools import BaseTool
    from langgraph.checkpoint.base import BaseCheckpointSaver
from drishti.api.schemas import ChatMessage
from drishti.config import Settings
from drishti.generation.models import RAGAnswer, StreamEvent
from drishti.generation.pipeline import RAGPipeline


class AgentRunner:
    """Retrieve → grade → generate agent (LangGraph)."""

    def __init__(
        self,
        rag: RAGPipeline,
        settings: Settings,
        *,
        checkpointer: BaseCheckpointSaver[Any] | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        self._rag = rag
        self._settings = settings
        self._checkpointer = checkpointer
        self._tools = list(tools or [])
        graph = build_rag_graph(rag, rag.llm, tools=self._tools)
        self._graph = graph.compile(checkpointer=checkpointer)

    @property
    def tools(self) -> list[BaseTool]:
        """LangChain tools wired into the optional tools graph node."""
        return self._tools

    def ask(
        self,
        question: str,
        *,
        filters: dict[str, str] | None = None,
        conversation_history: list[ChatMessage] | None = None,
        workspace_memory: str = "",
        thread_id: str | None = None,
    ) -> RAGAnswer:
        final = self._graph.invoke(
            self._initial_state(
                question,
                filters=filters,
                conversation_history=conversation_history,
                workspace_memory=workspace_memory,
            ),
            config=self._invoke_config(thread_id),
        )
        chunks = final.get("context_chunks") or ()
        return RAGAnswer(
            question=question.strip(),
            answer=str(final.get("answer", "")),
            citations=tuple(final.get("citations") or []),
            context_chunks=chunks,
        )

    async def ask_stream(
        self,
        question: str,
        *,
        filters: dict[str, str] | None = None,
        conversation_history: list[ChatMessage] | None = None,
        workspace_memory: str = "",
        thread_id: str | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream SSE events via LangGraph ``astream`` (updates + custom token chunks)."""
        started = time.perf_counter()
        state = initial_stream_state(
            self._initial_state(
                question,
                filters=filters,
                conversation_history=conversation_history,
                workspace_memory=workspace_memory,
            ),
        )
        graph_stream = self._graph.astream(
            state,
            config=self._invoke_config(thread_id),
            stream_mode=["updates", "custom"],
        )
        async for event in iter_sse_from_graph_stream(graph_stream, started_perf=started):
            yield event

    def _invoke_config(self, thread_id: str | None) -> RunnableConfig | None:
        if thread_id and self._checkpointer is not None:
            return {"configurable": {"thread_id": thread_id}}
        return None

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
            "retrieval_pass": 0,  # nosec B105 — counter, not a credential
            "query_expanded": False,
            "retry_mode": "",
            "tools_invoked": False,
            "stream_tokens": False,
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
