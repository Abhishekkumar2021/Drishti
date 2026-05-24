"""Unit tests for symbol metadata enrichment (US-03.07-03.09)."""

from __future__ import annotations

from pathlib import Path

import pytest

from drishti.ingestion.ast.metadata import build_context_path, resolve_parent_module
from drishti.ingestion.ast.python import PythonParser
from drishti.ingestion.symbols import SymbolTable

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "python" / "sample_module.py"


class TestMetadataEnrichment:
    @pytest.fixture
    def parser(self) -> PythonParser:
        return PythonParser.from_package()

    def test_class_docstring_and_context_path(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, "src/auth/service.py")
        auth_class = next(chunk for chunk in chunks if chunk.name == "AuthService")

        assert auth_class.docstring == "Authenticates users."
        assert auth_class.context_path == "src/auth/service.py::src.auth.service::AuthService"
        assert auth_class.parent_module == "src.auth.service"
        assert auth_class.definition_file_path == "src/auth/service.py"

    def test_callable_parameters_and_return_type(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        verify = next(chunk for chunk in chunks if chunk.name == "verify")

        assert verify.parameters == ["self", "token: str"]
        assert verify.return_type == "bool"
        assert verify.parent_class == "AuthService"
        assert verify.context_path.endswith("::AuthService::verify")

    def test_standalone_function_docstring(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())
        helper = next(chunk for chunk in chunks if chunk.name == "standalone_helper")

        assert helper.docstring == "Top-level helper."
        assert helper.parent_class is None

    def test_cyclomatic_complexity_counts_decision_points(self, parser: PythonParser) -> None:
        source = b"""def complex(value: int) -> int:
    if value < 0:
        return 0
    total = 0
    for item in range(value):
        if item % 2 == 0:
            total += item
    return total
"""
        chunks = parser.parse(source, "complex.py")
        fn = chunks[0]

        assert fn.cyclomatic_complexity == 4

    def test_imported_symbols_include_module_and_names(self, parser: PythonParser) -> None:
        source = FIXTURE.read_bytes()
        chunks = parser.parse(source, FIXTURE.as_posix())

        assert all("dataclasses" in chunk.imported_symbols for chunk in chunks)

    def test_java_method_parent_module_uses_package(self) -> None:
        from drishti.ingestion.ast.java import JavaParser

        fixture = Path(__file__).resolve().parent.parent / "fixtures" / "java" / "AuthService.java"
        parser = JavaParser.from_package()
        chunks = parser.parse(fixture.read_bytes(), "AuthService.java")
        method = next(
            chunk
            for chunk in chunks
            if chunk.name == "validate" and chunk.parent_class == "AuthService"
        )

        assert method.parent_module == "com.example.auth"
        assert method.context_path == "AuthService.java::AuthService::validate"
        assert method.return_type == "boolean"
        assert "String token" in method.parameters[0]


class TestMetadataHelpers:
    def test_resolve_parent_module_from_package(self) -> None:
        assert resolve_parent_module("src/Foo.java", "com.example") == "com.example"

    def test_build_context_path_with_parent_class(self) -> None:
        path = build_context_path(
            file_path="a.py",
            symbol_name="run",
            parent_class="Worker",
            parent_module="pkg.worker",
        )
        assert path == "a.py::Worker::run"


class TestSymbolTable:
    def test_resolves_symbol_to_defining_file(self) -> None:
        parser = PythonParser.from_package()
        table = SymbolTable()
        chunks_a = parser.parse(b"class AuthService:\n    pass\n", "auth/service.py")
        chunks_b = parser.parse(
            b"from auth.service import AuthService\n\nclass Client:\n    pass\n",
            "client.py",
        )
        table.register_many(chunks_a)
        table.register_many(chunks_b)

        assert table.resolve("AuthService") == "auth/service.py"
        context = "auth/service.py::auth.service::AuthService"
        assert table.resolve_context(context) == "auth/service.py"
        assert table.resolve("Client") == "client.py"
