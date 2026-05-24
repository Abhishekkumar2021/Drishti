"""RAG generation data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

StreamEventType = Literal["context", "token", "citation", "done", "error"]


@dataclass(frozen=True)
class ContextChunk:
    """A retrieved chunk formatted for the LLM context window."""

    chunk_id: str
    file_path: str
    content: str
    start_line: int | None = None
    end_line: int | None = None
    language: str | None = None
    name: str | None = None
    node_type: str | None = None
    score: float = 0.0

    def citation_tag(self) -> str:
        """Return the canonical citation tag for this chunk."""
        if self.start_line is not None and self.end_line is not None:
            return f"[{self.file_path}:L{self.start_line}-{self.end_line}]"
        if self.start_line is not None:
            return f"[{self.file_path}:L{self.start_line}]"
        return f"[{self.file_path}]"


@dataclass(frozen=True)
class Citation:
    """A parsed citation referencing source code or documentation."""

    citation_tag: str
    file_path: str
    start_line: int | None = None
    end_line: int | None = None
    valid: bool = True


@dataclass(frozen=True)
class StreamEvent:
    """Server-sent event emitted during streaming generation."""

    event: StreamEventType
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RAGAnswer:
    """Completed non-streaming RAG response."""

    question: str
    answer: str
    citations: tuple[Citation, ...]
    context_chunks: tuple[ContextChunk, ...]
