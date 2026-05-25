"""Unit tests for intelligent content routing."""

from __future__ import annotations

import pytest

from drishti.ingestion.content_router import ContentRouter
from drishti.ingestion.documents.pdf import build_minimal_pdf_bytes
from drishti.utils.language import LanguageRegistry

pytestmark = pytest.mark.unit


def _router() -> ContentRouter:
    registry = LanguageRegistry()
    return ContentRouter(
        extension_map=registry.extension_map,
        parser_extensions=frozenset(
            {".py", ".java", ".js", ".ts", ".go", ".md", ".pdf", ".yaml", ".yml", ".json"},
        ),
    )


class TestContentRouter:
    def test_detects_pdf_by_magic_not_extension(self) -> None:
        router = _router()
        pdf_bytes = build_minimal_pdf_bytes(pages=["Secret spec"])
        result = router.classify("uploads/spec.bin", pdf_bytes)
        assert result.kind == "pdf"
        assert result.effective_extension == ".pdf"
        assert result.detection_method == "magic_bytes"

    def test_detects_openapi_in_yaml_by_content(self) -> None:
        router = _router()
        text = b"openapi: 3.0.3\ninfo:\n  title: API\npaths: {}\n"
        result = router.classify("api/service.yaml", text)
        assert result.kind == "openapi"
        assert result.detection_method == "content_sniff"

    def test_detects_markdown_readme_without_extension(self) -> None:
        router = _router()
        text = b"# Architecture\n\nSystem overview.\n"
        result = router.classify("README", text)
        assert result.kind == "markdown"
        assert result.effective_extension == ".md"
