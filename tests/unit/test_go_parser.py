"""Unit tests for Go Tree-sitter parser (US-03.05)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import tree_sitter_go as tsgo
from tree_sitter import Language, Node, Parser, Query, QueryCursor

from drishti.ingestion.ast.go import GoParser
from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.ast.rules import LanguageRule, ParserRules
from drishti.ingestion.base import ParserRegistry

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "go" / "auth.go"


def _type_declaration_nodes(source: bytes) -> dict[str, Node]:
    language = Language(tsgo.language())
    tree = Parser(language).parse(source)
    query = Query(language, GoParser.load_query("go.scm"))
    nodes: dict[str, Node] = {}
    for _pattern_index, capture_map in QueryCursor(query).matches(tree.root_node):
        chunk_nodes = capture_map.get("chunk_node", [])
        symbol_nodes = capture_map.get("symbol_name", [])
        for index, node in enumerate(chunk_nodes):
            if node.type != "type_declaration":
                continue
            symbol_node = symbol_nodes[index] if index < len(symbol_nodes) else None
            if symbol_node is None:
                continue
            nodes[symbol_node.text.decode()] = node
    return nodes


class TestGoParser:
    @pytest.fixture
    def parser(self) -> GoParser:
        return GoParser.from_package()

    def test_parses_fixture_symbols(self, parser: GoParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, "internal/auth/service.go")
        names = {chunk.name for chunk in chunks}

        assert names >= {
            "auth",
            "Token",
            "Validator",
            "AuthService",
            "NewAuthService",
            "Validate",
        }

    def test_package_name_on_all_chunks(self, parser: GoParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())

        assert all(chunk.package_name == "auth" for chunk in chunks)

    def test_collects_import_paths(self, parser: GoParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())

        assert all({"context", "fmt"}.issubset(set(chunk.dependencies)) for chunk in chunks)

    def test_struct_and_interface_declarations(self, parser: GoParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        token = next(chunk for chunk in chunks if chunk.name == "Token")
        validator = next(chunk for chunk in chunks if chunk.name == "Validator")
        auth_struct = next(chunk for chunk in chunks if chunk.name == "AuthService")

        assert token.node_type == "type_declaration"
        assert "type Token string" in token.content
        assert validator.node_type == "type_declaration"
        assert "interface" in validator.content
        assert auth_struct.node_type == "type_declaration"
        assert "struct" in auth_struct.content

    def test_interface_and_struct_helpers(self, parser: GoParser) -> None:
        source = FIXTURE.read_bytes()
        type_nodes = _type_declaration_nodes(source)

        assert parser.is_interface_type(type_nodes["Validator"], source) is True
        assert parser.is_struct_type(type_nodes["AuthService"], source) is True
        assert parser.is_struct_type(type_nodes["Token"], source) is False

    def test_method_receiver_parent_scope(self, parser: GoParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        validate = next(chunk for chunk in chunks if chunk.name == "Validate")

        assert validate.node_type == "method_declaration"
        assert validate.parent_class == "AuthService"
        assert "func (s *AuthService) Validate" in validate.content.replace("\n", " ")

    def test_function_declaration_content(self, parser: GoParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        ctor = next(chunk for chunk in chunks if chunk.name == "NewAuthService")

        assert ctor.node_type == "function_declaration"
        assert "NewAuthService(issuer string)" in ctor.content.replace("\n", " ")

    def test_line_bounds_are_one_indexed(self, parser: GoParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        auth_struct = next(chunk for chunk in chunks if chunk.name == "AuthService")

        assert auth_struct.start_line is not None
        assert auth_struct.end_line is not None
        assert auth_struct.end_line >= auth_struct.start_line

    def test_empty_file_returns_no_chunks(self, parser: GoParser) -> None:
        assert parser.parse(b"", "empty.go") == []

    def test_last_modified_kwarg_is_propagated(self, parser: GoParser) -> None:
        modified = datetime(2024, 7, 1, tzinfo=UTC)
        chunks = parser.parse(b"package main\nfunc main() {}\n", "main.go", last_modified=modified)
        assert chunks[0].last_modified == modified

    def test_skips_short_nested_methods_when_below_threshold(self) -> None:
        rules = ParserRules(
            version=1,
            default_min_chunk_lines=3,
            languages={"go": LanguageRule("go", "go.scm", 3)},
        )
        parser = GoParser.from_rules(rules)
        source = b"""package auth

type AuthService struct{}

func (s *AuthService) Tiny() int { return 0 }
"""
        chunks = parser.parse(source, "service.go")
        assert {chunk.name for chunk in chunks} == {"auth", "AuthService"}

    def test_keeps_short_top_level_symbols(self, parser: GoParser) -> None:
        source = b"package main\n\ntype Token string\n"
        chunks = parser.parse(source, "tokens.go")
        token = next(chunk for chunk in chunks if chunk.name == "Token")
        assert token.parent_class is None


class TestParserRegistryIntegration:
    def test_default_registry_registers_go_extension(self) -> None:
        registry = create_default_parser_registry()
        assert ".go" in registry.registered_extensions()

    def test_registry_returns_go_parser(self) -> None:
        registry: ParserRegistry = create_default_parser_registry()
        parser = registry.get_parser("internal/auth/service.go")
        assert isinstance(parser, GoParser)
