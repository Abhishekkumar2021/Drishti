"""Unit tests for Python Tree-sitter parser (US-03.02)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from drishti.ingestion.ast.python import PythonParser
from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.base import ParserRegistry

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "python" / "sample_module.py"


class TestPythonParser:
    @pytest.fixture
    def parser(self) -> PythonParser:
        return PythonParser.from_package()

    def test_parses_fixture_module(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, "src/auth/service.py")

        assert len(chunks) == 4
        names = {chunk.name for chunk in chunks}
        assert names == {"AuthService", "verify", "is_active", "standalone_helper"}

    def test_line_bounds_match_fixture(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        expected = {
            "AuthService": (6, 15),
            "verify": (10, 11),
            "is_active": (13, 15),
            "standalone_helper": (18, 20),
        }
        for chunk in chunks:
            assert chunk.name in expected
            assert (chunk.start_line, chunk.end_line) == expected[chunk.name]

    def test_last_modified_kwarg_is_propagated(self, parser: PythonParser) -> None:
        modified = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)
        chunks = parser.parse(b"class A:\n    pass\n", "a.py", last_modified=modified)
        assert chunks[0].last_modified == modified

    def test_extracts_decorators_on_class(self, parser: PythonParser) -> None:
        source = b"@dataclass\nclass Foo:\n    pass\n"
        chunks = parser.parse(source, "foo.py")
        foo = next(chunk for chunk in chunks if chunk.name == "Foo")

        assert "dataclass" in foo.decorators
        assert "@dataclass" in foo.content

    def test_extracts_decorators_on_method(self, parser: PythonParser) -> None:
        source = b"class Box:\n    @property\n    def size(self):\n        return 1\n"
        chunks = parser.parse(source, "box.py")
        size = next(chunk for chunk in chunks if chunk.name == "size")

        assert "property" in size.decorators
        assert "@property" in size.content
        assert size.parent_class == "Box"

    def test_parent_class_for_methods(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        verify = next(chunk for chunk in chunks if chunk.name == "verify")

        assert verify.parent_class == "AuthService"
        assert verify.node_type == "function_definition"
        assert verify.language == "python"

    def test_class_chunk_has_no_parent_class(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        auth_class = next(chunk for chunk in chunks if chunk.name == "AuthService")

        assert auth_class.parent_class is None
        assert auth_class.node_type == "class_definition"

    def test_empty_file_returns_no_chunks(self, parser: PythonParser) -> None:
        assert parser.parse(b"", "empty.py") == []

    def test_async_function_is_extracted(self, parser: PythonParser) -> None:
        source = b"async def fetch():\n    return None\n"
        chunks = parser.parse(source, "async.py")
        assert len(chunks) == 1
        assert chunks[0].name == "fetch"
        assert chunks[0].node_type == "function_definition"

    def test_skips_symbols_with_parse_errors(self, parser: PythonParser) -> None:
        source = b"class Broken:\n    def ok(self):\n        return 1\n    def bad(\n"
        chunks = parser.parse(source, "broken.py")
        names = {chunk.name for chunk in chunks}
        assert names == {"ok"}

    def test_chunks_sorted_by_start_line(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        lines = [chunk.start_line or 0 for chunk in chunks]

        assert lines == sorted(lines)


class TestParserRegistryIntegration:
    def test_default_registry_registers_python_extensions(self) -> None:
        registry = create_default_parser_registry()
        assert frozenset({".py", ".pyi", ".pyw"}).issubset(registry.registered_extensions())

    def test_registry_returns_python_parser(self) -> None:
        registry: ParserRegistry = create_default_parser_registry()
        parser = registry.get_parser("module.pyi")
        assert isinstance(parser, PythonParser)
