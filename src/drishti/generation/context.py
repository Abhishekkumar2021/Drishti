"""Context builder for RAG prompts (US-07.01)."""

from __future__ import annotations

from drishti.generation.models import ContextChunk
from drishti.search.models import SearchHit


class ContextBuilder:
    """Format search hits into bounded LLM context envelopes."""

    def __init__(self, *, max_chars: int = 120_000, max_chunks: int = 15) -> None:
        self._max_chars = max(1, max_chars)
        self._max_chunks = max(1, max_chunks)

    def build_from_hits(self, hits: list[SearchHit]) -> tuple[ContextChunk, ...]:
        """Convert search hits to context chunks respecting size limits."""
        selected: list[ContextChunk] = []
        total_chars = 0

        for hit in hits[: self._max_chunks]:
            chunk = _hit_to_context_chunk(hit)
            block_len = len(chunk.content) + len(chunk.file_path) + 128
            if selected and total_chars + block_len > self._max_chars:
                break
            selected.append(chunk)
            total_chars += block_len

        return tuple(selected)

    def render_xml(self, chunks: tuple[ContextChunk, ...] | list[ContextChunk]) -> str:
        """Render context chunks as XML-style delimited blocks."""
        if not chunks:
            return '<context empty="true">No relevant context was retrieved.</context>'

        blocks: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            attrs = [
                f'id="{index}"',
                f'chunk_id="{_xml_attr(chunk.chunk_id)}"',
                f'file="{_xml_attr(chunk.file_path)}"',
            ]
            if chunk.start_line is not None:
                attrs.append(f'start="{chunk.start_line}"')
            if chunk.end_line is not None:
                attrs.append(f'end="{chunk.end_line}"')
            if chunk.language:
                attrs.append(f'language="{_xml_attr(chunk.language)}"')
            if chunk.name:
                attrs.append(f'name="{_xml_attr(chunk.name)}"')
            attr_str = " ".join(attrs)
            blocks.append(
                f"<context {attr_str}>\n{chunk.content}\n</context>",
            )
        return "\n\n".join(blocks)


def _hit_to_context_chunk(hit: SearchHit) -> ContextChunk:
    payload = hit.payload
    return ContextChunk(
        chunk_id=hit.chunk_id,
        file_path=str(payload.get("file_path") or ""),
        content=hit.content,
        start_line=_optional_int(payload.get("start_line")),
        end_line=_optional_int(payload.get("end_line")),
        language=_optional_str(payload.get("language")),
        name=_optional_str(payload.get("name")),
        node_type=_optional_str(payload.get("node_type")),
        score=hit.score,
    )


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _xml_attr(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;")


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
