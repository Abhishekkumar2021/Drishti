"""Citation parsing and validation (US-07.04)."""

from __future__ import annotations

import re

from drishti.generation.models import Citation, ContextChunk

_CITATION_PATTERN = re.compile(
    r"\[(?P<file_path>[^\]:]+):L(?P<start>\d+)(?:-(?P<end>\d+))?\]",
)

_CITATION_PATTERN_FILE_ONLY = re.compile(r"\[(?P<file_path>[^\]:]+)\]")


def parse_citations(text: str) -> list[Citation]:
    """Extract citation tags from generated answer text."""
    found: list[Citation] = []
    seen: set[str] = set()

    for match in _CITATION_PATTERN.finditer(text):
        tag = match.group(0)
        if tag in seen:
            continue
        seen.add(tag)
        end_line = int(match.group("end")) if match.group("end") else int(match.group("start"))
        found.append(
            Citation(
                citation_tag=tag,
                file_path=match.group("file_path").strip(),
                start_line=int(match.group("start")),
                end_line=end_line,
            ),
        )

    for match in _CITATION_PATTERN_FILE_ONLY.finditer(text):
        tag = match.group(0)
        if tag in seen or ":L" in tag:
            continue
        seen.add(tag)
        found.append(
            Citation(
                citation_tag=tag,
                file_path=match.group("file_path").strip(),
            ),
        )

    return found


def validate_citations(
    citations: list[Citation],
    context_chunks: tuple[ContextChunk, ...] | list[ContextChunk],
) -> list[Citation]:
    """Mark citations invalid when they do not match retrieved context."""
    if not citations:
        return []

    allowed_files = {chunk.file_path for chunk in context_chunks}
    validated: list[Citation] = []

    for citation in citations:
        file_ok = citation.file_path in allowed_files
        line_ok = True
        if citation.start_line is not None and file_ok:
            line_ok = _line_in_context(citation, context_chunks)
        validated.append(
            Citation(
                citation_tag=citation.citation_tag,
                file_path=citation.file_path,
                start_line=citation.start_line,
                end_line=citation.end_line,
                valid=file_ok and line_ok,
            ),
        )

    return validated


def filter_valid_citations(citations: list[Citation]) -> list[Citation]:
    """Return only citations that passed validation."""
    return [citation for citation in citations if citation.valid]


def _line_in_context(
    citation: Citation,
    context_chunks: tuple[ContextChunk, ...] | list[ContextChunk],
) -> bool:
    for chunk in context_chunks:
        if chunk.file_path != citation.file_path:
            continue
        if chunk.start_line is None or chunk.end_line is None:
            return True
        if citation.start_line is None:
            return True
        cited_end = citation.end_line or citation.start_line
        return chunk.start_line <= citation.start_line and cited_end <= chunk.end_line
    return False
