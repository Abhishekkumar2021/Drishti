"""Markdown header-hierarchy parser (US-04.03)."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from drishti.api.schemas import UniversalChunk
from drishti.ingestion.base import BaseParser

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_DEFAULT_MIN_LINES = 1


@dataclass(frozen=True)
class _Section:
    """A markdown section bounded by headings."""

    level: int
    title: str
    context_path: str
    body_lines: tuple[str, ...]
    start_line: int
    end_line: int


class MarkdownParser(BaseParser):
    """Chunks markdown files by ATX headings while preserving parent section context."""

    def __init__(self, *, min_body_lines: int = _DEFAULT_MIN_LINES) -> None:
        self._min_body_lines = max(1, min_body_lines)

    def parse(
        self,
        file_content: bytes,
        file_path: str,
        *,
        last_modified: datetime | None = None,
    ) -> list[UniversalChunk]:
        text = file_content.decode("utf-8", errors="replace")
        source_id = hashlib.sha256(file_content).hexdigest()
        indexed_at = last_modified if last_modified is not None else datetime.now(UTC)
        sections = _split_by_headings(text)
        chunks: list[UniversalChunk] = []

        for section in sections:
            body = "\n".join(section.body_lines).strip()
            if not body:
                continue
            line_count = len([line for line in section.body_lines if line.strip()])
            if line_count < self._min_body_lines and section.level > 0:
                continue

            chunks.append(
                UniversalChunk(
                    id=str(uuid.uuid4()),
                    source_id=source_id,
                    content=body,
                    content_type="text",
                    file_path=file_path,
                    source_type="markdown",
                    language="markdown",
                    start_line=section.start_line,
                    end_line=section.end_line,
                    node_type=f"h{section.level}" if section.level else "document",
                    name=section.title or None,
                    context_path=section.context_path or None,
                    docstring=section.context_path if section.level else None,
                    last_modified=indexed_at,
                )
            )

        return chunks


def _split_by_headings(text: str) -> list[_Section]:
    """Split markdown into sections using ``#`` … ``######`` headings."""
    lines = text.splitlines()
    if not lines:
        return []

    heading_stack: list[tuple[int, str]] = []
    body_lines: list[str] = []
    section_start = 1
    sections: list[_Section] = []

    def flush(level: int, title: str, end_line: int) -> None:
        nonlocal body_lines, section_start
        if not body_lines and level == 0:
            return
        context = _context_path(heading_stack)
        sections.append(
            _Section(
                level=level,
                title=title,
                context_path=context,
                body_lines=tuple(body_lines),
                start_line=section_start,
                end_line=max(section_start, end_line),
            ),
        )
        body_lines = []

    for line_no, line in enumerate(lines, start=1):
        match = _HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            flush(
                heading_stack[-1][0] if heading_stack else 0,
                heading_stack[-1][1] if heading_stack else "",
                line_no - 1,
            )
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
            body_lines = []
            section_start = line_no + 1
            continue
        body_lines.append(line)

    if body_lines or not sections:
        leaf_level, leaf_title = heading_stack[-1] if heading_stack else (0, "")
        flush(leaf_level, leaf_title, len(lines))

    if not sections and text.strip():
        sections.append(
            _Section(
                level=0,
                title="",
                context_path="",
                body_lines=tuple(lines),
                start_line=1,
                end_line=len(lines),
            ),
        )

    return sections


def _context_path(heading_stack: list[tuple[int, str]]) -> str:
    if not heading_stack:
        return ""
    return " > ".join(title for _level, title in heading_stack)
