"""Unit tests for parser registry."""

from __future__ import annotations

from datetime import datetime

import pytest

from drishti.api.schemas import UniversalChunk
from drishti.ingestion.base import BaseParser, ParserRegistry

pytestmark = pytest.mark.unit


class StubParser(BaseParser):
    def parse(
        self,
        file_content: bytes,
        file_path: str,
        *,
        last_modified: datetime | None = None,
    ) -> list[UniversalChunk]:
        return []


class TestParserRegistry:
    def test_registers_and_retrieves_parser(self) -> None:
        registry = ParserRegistry()
        parser = StubParser()
        registry.register(".py", parser)
        assert registry.get_parser("src/main.py") is parser

    def test_raises_for_unknown_extension(self) -> None:
        registry = ParserRegistry()
        with pytest.raises(ValueError, match="Could not resolve file extension"):
            registry.get_parser("README")

    def test_registered_extensions(self) -> None:
        registry = ParserRegistry()
        registry.register(".go", StubParser())
        assert registry.registered_extensions() == frozenset({".go"})
