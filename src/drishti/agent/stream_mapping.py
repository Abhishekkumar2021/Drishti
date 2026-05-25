"""Map LangGraph stream payloads to Drishti SSE events."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from drishti.agent.state import AgentState
from drishti.generation.models import StreamEvent
from drishti.generation.streaming import citation_event, context_event, done_event, token_event


async def iter_sse_from_graph_stream(
    graph_stream: AsyncIterator[Any],
    *,
    started_perf: float,
    token_count_start: int = 0,
) -> AsyncIterator[StreamEvent]:
    """Translate ``graph.astream(..., stream_mode=['updates', 'custom'])`` into SSE events."""
    import time

    token_count = token_count_start

    async for chunk in graph_stream:
        if not isinstance(chunk, tuple) or len(chunk) != 2:
            continue
        mode, payload = chunk[0], chunk[1]
        if mode == "custom" and isinstance(payload, dict):
            if payload.get("event") == "token":
                text = str(payload.get("text", ""))
                if text:
                    token_count += 1
                    yield token_event(text)
            continue

        if mode != "updates" or not isinstance(payload, dict):
            continue

        for node_name, update in payload.items():
            if not isinstance(update, dict):
                continue
            if node_name == "retrieve" and "context_chunks" in update:
                chunks = update.get("context_chunks") or ()
                yield context_event(chunks)
            if node_name == "generate" and update.get("citations"):
                for citation in update["citations"]:
                    yield citation_event(citation)

    elapsed_ms = int((time.perf_counter() - started_perf) * 1000)
    yield done_event(total_tokens=token_count, execution_time_ms=elapsed_ms)


def initial_stream_state(base: AgentState) -> AgentState:
    """Mark state so the generate node emits token chunks via ``get_stream_writer``."""
    return {**base, "stream_tokens": True}
