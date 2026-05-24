"""Unit tests for JavaScript Tree-sitter parser (US-03.04)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from drishti.ingestion.ast.ecmascript import EcmaScriptParser
from drishti.ingestion.ast.javascript import JavaScriptParser
from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.base import ParserRegistry

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "javascript" / "auth.js"


class TestJavaScriptParser:
    @pytest.fixture
    def parser(self) -> JavaScriptParser:
        return JavaScriptParser.from_package()

    def test_parses_fixture_symbols(self, parser: JavaScriptParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, "src/auth.js")
        names = {chunk.name for chunk in chunks}

        assert names >= {"AuthService", "verify", "fetchUser", "useAuth", "App", "ArrowHelper"}

    def test_module_imports_on_chunks(self, parser: JavaScriptParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())

        assert all("react" in chunk.dependencies for chunk in chunks)

    def test_export_modifiers(self, parser: JavaScriptParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        app = next(chunk for chunk in chunks if chunk.name == "App")

        assert "export" in app.exports
        assert "default" in app.exports
        assert "export default" in app.content

    def test_class_method_parent_scope(self, parser: JavaScriptParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        verify = next(chunk for chunk in chunks if chunk.name == "verify")

        assert verify.parent_class == "AuthService"
        assert verify.node_type == "method_definition"

    def test_arrow_function_chunk(self, parser: JavaScriptParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        arrow = next(chunk for chunk in chunks if chunk.name == "ArrowHelper")

        assert arrow.node_type == "lexical_declaration"
        assert "=>" in arrow.content

    def test_react_hook_detection_helper(self) -> None:
        assert EcmaScriptParser.is_react_hook("useAuth", "function_declaration") is True
        assert EcmaScriptParser.is_react_hook("App", "function_declaration") is False

    def test_line_bounds_are_one_indexed(self, parser: JavaScriptParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        auth_class = next(chunk for chunk in chunks if chunk.name == "AuthService")

        assert auth_class.start_line is not None
        assert auth_class.end_line is not None
        assert auth_class.end_line >= auth_class.start_line

    def test_empty_file_returns_no_chunks(self, parser: JavaScriptParser) -> None:
        assert parser.parse(b"", "empty.js") == []

    def test_last_modified_kwarg_is_propagated(self, parser: JavaScriptParser) -> None:
        modified = datetime(2024, 3, 1, tzinfo=UTC)
        chunks = parser.parse(b"export function fn() {}\n", "fn.js", last_modified=modified)
        assert chunks[0].last_modified == modified


class TestParserRegistryIntegration:
    def test_default_registry_registers_javascript_extensions(self) -> None:
        registry = create_default_parser_registry()
        for ext in (".js", ".jsx", ".mjs", ".cjs"):
            assert ext in registry.registered_extensions()

    def test_registry_returns_javascript_parser(self) -> None:
        registry: ParserRegistry = create_default_parser_registry()
        parser = registry.get_parser("component.jsx")
        assert isinstance(parser, JavaScriptParser)
