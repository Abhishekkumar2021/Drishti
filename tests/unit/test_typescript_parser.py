"""Unit tests for TypeScript / TSX Tree-sitter parsers (US-03.04)."""

from __future__ import annotations

from pathlib import Path

import pytest

from drishti.ingestion.ast.ecmascript import EcmaScriptParser
from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.ast.typescript import TypeScriptParser
from drishti.ingestion.base import ParserRegistry

pytestmark = pytest.mark.unit

TS_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "typescript" / "AuthPanel.ts"
TSX_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "typescript" / "App.tsx"


@pytest.fixture
def parser() -> TypeScriptParser:
    return TypeScriptParser.from_package()


@pytest.fixture
def tsx_parser() -> TypeScriptParser:
    return TypeScriptParser.for_tsx()


class TestTypeScriptParser:
    def test_parses_interfaces_and_types(self, parser: TypeScriptParser) -> None:
        source = TS_FIXTURE.read_bytes()
        chunks = parser.parse(source, TS_FIXTURE.as_posix())
        names = {chunk.name for chunk in chunks}

        assert "PanelProps" in names
        assert "Status" in names
        props = next(chunk for chunk in chunks if chunk.name == "PanelProps")
        assert props.node_type == "interface_declaration"

        status = next(chunk for chunk in chunks if chunk.name == "Status")
        assert status.node_type == "type_alias_declaration"

    def test_parses_class_and_methods(self, parser: TypeScriptParser) -> None:
        source = TS_FIXTURE.read_bytes()
        chunks = parser.parse(source, TS_FIXTURE.as_posix())
        panel = next(chunk for chunk in chunks if chunk.name == "AuthPanel")
        verify = next(chunk for chunk in chunks if chunk.name == "verify")

        assert panel.node_type == "class_declaration"
        assert verify.parent_class == "AuthPanel"
        assert "verify(userId: string): boolean" in verify.content.replace("\n", " ")

    def test_module_imports_from_types(self, parser: TypeScriptParser) -> None:
        source = TS_FIXTURE.read_bytes()
        chunks = parser.parse(source, TS_FIXTURE.as_posix())

        assert all("./types" in chunk.dependencies for chunk in chunks)

    def test_export_on_named_symbol(self, parser: TypeScriptParser) -> None:
        source = TS_FIXTURE.read_bytes()
        chunks = parser.parse(source, TS_FIXTURE.as_posix())
        hook = next(chunk for chunk in chunks if chunk.name == "usePanelState")

        assert "export" in hook.exports
        assert EcmaScriptParser.is_react_hook(hook.name or "", hook.node_type or "")


class TestTsxParser:
    def test_parses_react_component_in_tsx(self, tsx_parser: TypeScriptParser) -> None:
        source = TSX_FIXTURE.read_bytes()
        chunks = tsx_parser.parse(source, TSX_FIXTURE.as_posix())
        app_fn = next(
            chunk
            for chunk in chunks
            if chunk.name == "App" and chunk.node_type == "function_declaration"
        )

        assert "export" in app_fn.exports
        assert "<div>" in app_fn.content

    def test_tsx_interface_export(self, tsx_parser: TypeScriptParser) -> None:
        source = TSX_FIXTURE.read_bytes()
        chunks = tsx_parser.parse(source, TSX_FIXTURE.as_posix())
        props = next(chunk for chunk in chunks if chunk.name == "AppProps")

        assert props.node_type == "interface_declaration"
        assert "react" in props.dependencies


class TestParserRegistryIntegration:
    def test_registry_registers_typescript_extensions(self) -> None:
        registry = create_default_parser_registry()
        assert ".ts" in registry.registered_extensions()
        assert ".tsx" in registry.registered_extensions()

    def test_registry_uses_distinct_instances_for_ts_and_tsx(self) -> None:
        registry: ParserRegistry = create_default_parser_registry()
        ts_parser = registry.get_parser("panel.ts")
        tsx_parser = registry.get_parser("App.tsx")
        assert isinstance(ts_parser, TypeScriptParser)
        assert isinstance(tsx_parser, TypeScriptParser)
        assert ts_parser is not tsx_parser
