"""Unit tests for citation parsing (US-07.04)."""

from __future__ import annotations

import pytest

from drishti.generation.citations import parse_citations, validate_citations
from drishti.generation.models import ContextChunk

pytestmark = pytest.mark.unit


class TestCitationParser:
    def test_parses_line_range_citation(self) -> None:
        text = "See [src/auth/token.py:L25-40] for details."
        citations = parse_citations(text)
        assert len(citations) == 1
        assert citations[0].file_path == "src/auth/token.py"
        assert citations[0].start_line == 25
        assert citations[0].end_line == 40

    def test_validates_against_context(self) -> None:
        context = (
            ContextChunk(
                chunk_id="c1",
                file_path="src/auth/token.py",
                content="code",
                start_line=25,
                end_line=40,
            ),
        )
        citations = parse_citations("Ref [src/auth/token.py:L25-40]")
        validated = validate_citations(citations, context)
        assert validated[0].valid is True

    def test_rejects_unknown_file(self) -> None:
        context = (
            ContextChunk(
                chunk_id="c1",
                file_path="src/auth/token.py",
                content="code",
                start_line=1,
                end_line=5,
            ),
        )
        citations = parse_citations("Ref [src/other.py:L1-5]")
        validated = validate_citations(citations, context)
        assert validated[0].valid is False
