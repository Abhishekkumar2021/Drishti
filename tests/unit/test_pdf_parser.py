"""Unit tests for PDF document ingestion (US-04.01, US-04.02)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from drishti.ingestion.documents.pdf import (
    PdfParser,
    _rows_to_markdown_table,
    build_minimal_pdf_bytes,
)

pytestmark = pytest.mark.unit


class TestPdfParser:
    def test_extracts_text_blocks_with_page_numbers(self) -> None:
        pdf_bytes = build_minimal_pdf_bytes(pages=["Authentication overview"])
        parser = PdfParser()
        chunks = parser.parse(
            pdf_bytes,
            "docs/auth-spec.pdf",
            last_modified=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert chunks
        assert any("Authentication" in chunk.content for chunk in chunks)
        assert all(chunk.source_type == "pdf" for chunk in chunks)
        assert all(chunk.page_number == 1 for chunk in chunks)

    def test_rows_to_markdown_table_format(self) -> None:
        markdown = _rows_to_markdown_table(
            [
                ["Name", "Value"],
                ["latency", "12ms"],
            ],
        )
        assert "| Name | Value |" in markdown
        assert "| latency | 12ms |" in markdown
