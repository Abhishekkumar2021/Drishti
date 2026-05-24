"""Unit tests for Java Tree-sitter parser (US-03.03)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from drishti.ingestion.ast.java import JavaParser
from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.base import ParserRegistry

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "java" / "AuthService.java"


class TestJavaParser:
    @pytest.fixture
    def parser(self) -> JavaParser:
        return JavaParser.from_package()

    def test_parses_fixture_symbols(self, parser: JavaParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, "src/main/java/com/example/auth/AuthService.java")

        names = {chunk.name for chunk in chunks}
        assert names >= {
            "com.example.auth",
            "TokenValidator",
            "AuthService",
            "issuer",
            "MAX_RETRIES",
            "validate",
        }

    def test_package_name_on_all_chunks(self, parser: JavaParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())

        assert all(chunk.package_name == "com.example.auth" for chunk in chunks)

    def test_extracts_package_declaration(self, parser: JavaParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        package = next(chunk for chunk in chunks if chunk.node_type == "package_declaration")

        assert package.name == "com.example.auth"
        assert "package com.example.auth" in package.content

    def test_field_chunks_preserve_declarations(self, parser: JavaParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        issuer = next(chunk for chunk in chunks if chunk.name == "issuer")

        assert issuer.node_type == "field_declaration"
        assert issuer.parent_class == "AuthService"
        assert "private final String issuer" in issuer.content

    def test_method_signature_in_content(self, parser: JavaParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        methods = [
            chunk
            for chunk in chunks
            if chunk.name == "validate" and chunk.node_type == "method_declaration"
        ]
        class_method = next(chunk for chunk in methods if chunk.parent_class == "AuthService")

        assert "boolean validate(String token)" in class_method.content.replace("\n", " ")
        assert "Override" in class_method.decorators
        assert "@Override" in class_method.content

    def test_interface_method_parent_scope(self, parser: JavaParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        iface_method = next(
            chunk
            for chunk in chunks
            if chunk.name == "validate"
            and chunk.parent_class == "TokenValidator"
            and chunk.node_type == "method_declaration"
        )

        assert "boolean validate(String token)" in iface_method.content

    def test_constructor_extracted(self, parser: JavaParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        ctor = next(chunk for chunk in chunks if chunk.node_type == "constructor_declaration")

        assert ctor.name == "AuthService"
        assert ctor.parent_class == "AuthService"
        assert "AuthService(String issuer)" in ctor.content.replace("\n", " ")

    def test_line_bounds_are_one_indexed(self, parser: JavaParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        auth_class = next(chunk for chunk in chunks if chunk.name == "AuthService")

        assert auth_class.start_line is not None
        assert auth_class.end_line is not None
        assert auth_class.start_line >= 1
        assert auth_class.end_line >= auth_class.start_line

    def test_empty_file_returns_no_chunks(self, parser: JavaParser) -> None:
        assert parser.parse(b"", "Empty.java") == []

    def test_last_modified_kwarg_is_propagated(self, parser: JavaParser) -> None:
        modified = datetime(2024, 6, 1, tzinfo=UTC)
        chunks = parser.parse(b"class A {}\n", "A.java", last_modified=modified)
        assert chunks[0].last_modified == modified


class TestParserRegistryIntegration:
    def test_default_registry_registers_java_extension(self) -> None:
        registry = create_default_parser_registry()
        assert ".java" in registry.registered_extensions()

    def test_registry_returns_java_parser(self) -> None:
        registry: ParserRegistry = create_default_parser_registry()
        parser = registry.get_parser("com/example/Demo.java")
        assert isinstance(parser, JavaParser)
