"""Unit tests for markdown document ingestion (US-04.03)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from drishti.ingestion.documents.markdown import MarkdownParser

pytestmark = pytest.mark.unit


SAMPLE = """\
# Architecture

Overview of the system.

## Authentication

Login uses JWT tokens.

### Token refresh

Refresh runs every 15 minutes.
"""


class TestMarkdownParser:
    def test_chunks_by_heading_hierarchy(self) -> None:
        parser = MarkdownParser(min_body_lines=1)
        chunks = parser.parse(
            SAMPLE.encode(),
            "docs/architecture.md",
            last_modified=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert len(chunks) >= 3
        auth = next(c for c in chunks if c.name == "Authentication")
        assert auth.source_type == "markdown"
        assert auth.content_type == "text"
        assert "JWT" in auth.content
        assert auth.context_path == "Architecture > Authentication"
        assert auth.start_line is not None

    def test_file_without_headings_becomes_single_chunk(self) -> None:
        parser = MarkdownParser()
        text = "Plain readme line one.\nLine two.\n"
        chunks = parser.parse(text.encode(), "README.md")
        assert len(chunks) == 1
        assert "Plain readme" in chunks[0].content
        assert chunks[0].node_type == "document"

    def test_empty_file_returns_no_chunks(self) -> None:
        parser = MarkdownParser()
        assert parser.parse(b"", "empty.md") == []
