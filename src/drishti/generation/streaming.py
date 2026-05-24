"""SSE formatting helpers for streaming RAG (US-07.03)."""

from __future__ import annotations

import json
from collections.abc import Iterator

from drishti.generation.models import Citation, ContextChunk, StreamEvent


def format_sse_event(event: StreamEvent) -> str:
    """Format a stream event as an SSE message block."""
    payload = json.dumps(event.data, ensure_ascii=False)
    return f"event: {event.event}\ndata: {payload}\n\n"


def context_event(chunks: tuple[ContextChunk, ...] | list[ContextChunk]) -> StreamEvent:
    """Build the initial context SSE event."""
    sources = [
        {
            "id": index,
            "chunk_id": chunk.chunk_id,
            "file_path": chunk.file_path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
        }
        for index, chunk in enumerate(chunks, start=1)
    ]
    return StreamEvent(event="context", data={"sources": sources})


def token_event(text: str) -> StreamEvent:
    """Build a token SSE event."""
    return StreamEvent(event="token", data={"text": text})


def citation_event(citation: Citation) -> StreamEvent:
    """Build a citation SSE event."""
    return StreamEvent(
        event="citation",
        data={
            "citation_tag": citation.citation_tag,
            "file_path": citation.file_path,
            "start_line": citation.start_line,
            "end_line": citation.end_line,
            "valid": citation.valid,
        },
    )


def done_event(*, total_tokens: int, execution_time_ms: int) -> StreamEvent:
    """Build the stream completion SSE event."""
    return StreamEvent(
        event="done",
        data={
            "total_tokens": total_tokens,
            "execution_time_ms": execution_time_ms,
        },
    )


def iter_sse_events(events: Iterator[StreamEvent]) -> Iterator[str]:
    """Yield formatted SSE strings from stream events."""
    for event in events:
        yield format_sse_event(event)
