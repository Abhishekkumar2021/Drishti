"""Unit tests for document parser registry wiring."""

from __future__ import annotations

import pytest

from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.git_changes import discover_parseable_files

pytestmark = pytest.mark.unit


class TestDocumentRegistry:
    def test_registry_includes_markdown_extensions(self) -> None:
        registry = create_default_parser_registry()
        assert ".md" in registry.registered_extensions()
        assert ".mdx" in registry.registered_extensions()

    def test_discover_includes_markdown_in_repo(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        registry = create_default_parser_registry()
        paths = discover_parseable_files(root, parser_registry=registry)
        md_paths = [path for path in paths if path.endswith(".md")]
        assert md_paths, "expected at least one markdown file in the repository"
