"""Unit tests for Tree-sitter parser rules and catalog (US-03.06)."""

from __future__ import annotations

import pytest

from drishti.ingestion.ast import (
    GoParser,
    JavaParser,
    JavaScriptParser,
    PythonParser,
    TypeScriptParser,
    build_production_parsers,
    load_parser_rules,
    supported_parser_extensions,
)
from drishti.ingestion.ast.rules import LanguageRule, ParserRules

pytestmark = pytest.mark.unit


class TestParserRules:
    def test_loads_packaged_rules(self) -> None:
        rules = load_parser_rules()
        assert rules.version >= 1
        assert rules.default_min_chunk_lines == 3
        assert set(rules.languages) >= {"python", "java", "javascript", "typescript", "go"}

    def test_query_file_for_known_language(self) -> None:
        rules = load_parser_rules()
        assert rules.query_file_for("python") == "python.scm"
        assert rules.query_file_for("go") == "go.scm"

    def test_query_file_for_unknown_language_raises(self) -> None:
        rules = ParserRules(version=1, default_min_chunk_lines=3, languages={})
        with pytest.raises(KeyError, match="kotlin"):
            rules.query_file_for("kotlin")

    def test_min_chunk_lines_fallback_to_default(self) -> None:
        rules = ParserRules(
            version=1,
            default_min_chunk_lines=5,
            languages={"python": LanguageRule("python", "python.scm", 4)},
        )
        assert rules.min_chunk_lines_for("python") == 4
        assert rules.min_chunk_lines_for("java") == 5


class TestParserCatalog:
    def test_supported_extensions_cover_all_production_parsers(self) -> None:
        extensions = supported_parser_extensions()
        assert ".go" in extensions
        assert ".tsx" in extensions
        assert ".pyi" in extensions

    def test_build_production_parsers_returns_all_languages(self) -> None:
        parsers = build_production_parsers()
        parser_types = {type(parser) for parser in parsers}
        assert parser_types == {
            PythonParser,
            JavaParser,
            JavaScriptParser,
            TypeScriptParser,
            GoParser,
        }

    def test_from_rules_uses_configured_thresholds(self) -> None:
        rules = ParserRules(
            version=1,
            default_min_chunk_lines=3,
            languages={
                "go": LanguageRule("go", "go.scm", 10),
            },
        )
        parser = GoParser.from_rules(rules)
        assert parser._min_chunk_lines == 10
