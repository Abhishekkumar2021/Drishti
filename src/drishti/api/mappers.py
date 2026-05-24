"""Map internal models to API response schemas."""

from __future__ import annotations

from drishti.api.responses import CitationItem, SearchResultItem
from drishti.generation.models import Citation, ContextChunk, RAGAnswer
from drishti.search.models import SearchHit


def search_hit_to_item(hit: SearchHit) -> SearchResultItem:
    """Convert a search hit to an API result item."""
    payload = hit.payload
    return SearchResultItem(
        chunk_id=hit.chunk_id,
        file_path=str(payload.get("file_path", "")),
        content=hit.content,
        score=hit.score,
        start_line=payload.get("start_line"),
        end_line=payload.get("end_line"),
        language=payload.get("language"),
        name=payload.get("name"),
        node_type=payload.get("node_type"),
    )


def citation_to_item(citation: Citation) -> CitationItem:
    """Convert a generation citation to an API item."""
    return CitationItem(
        citation_tag=citation.citation_tag,
        file_path=citation.file_path,
        start_line=citation.start_line,
        end_line=citation.end_line,
        valid=citation.valid,
    )


def context_chunk_to_item(chunk: ContextChunk) -> SearchResultItem:
    """Convert a RAG context chunk to a search result item."""
    return SearchResultItem(
        chunk_id=chunk.chunk_id,
        file_path=chunk.file_path,
        content=chunk.content,
        score=0.0,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        language=None,
        name=None,
        node_type=None,
    )


def rag_answer_to_sources(answer: RAGAnswer) -> list[SearchResultItem]:
    """Map context chunks used in a RAG answer to source items."""
    return [context_chunk_to_item(chunk) for chunk in answer.context_chunks]
