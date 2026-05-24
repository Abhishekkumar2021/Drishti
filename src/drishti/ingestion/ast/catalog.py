"""Production Tree-sitter parser catalog for all supported languages."""

from __future__ import annotations

from collections.abc import Callable

from drishti.ingestion.ast.go import GoParser
from drishti.ingestion.ast.java import JavaParser
from drishti.ingestion.ast.javascript import JavaScriptParser
from drishti.ingestion.ast.python import PythonParser
from drishti.ingestion.ast.rules import ParserRules, load_parser_rules
from drishti.ingestion.ast.typescript import TypeScriptParser
from drishti.ingestion.base import BaseParser

ParserFactory = Callable[[ParserRules], BaseParser]


def _python_factory(rules: ParserRules) -> PythonParser:
    return PythonParser.from_rules(rules)


def _java_factory(rules: ParserRules) -> JavaParser:
    return JavaParser.from_rules(rules)


def _javascript_factory(rules: ParserRules) -> JavaScriptParser:
    return JavaScriptParser.from_rules(rules)


def _typescript_factory(rules: ParserRules) -> TypeScriptParser:
    return TypeScriptParser.from_rules(rules)


def _tsx_factory(rules: ParserRules) -> TypeScriptParser:
    return TypeScriptParser.for_tsx(rules)


def _go_factory(rules: ParserRules) -> GoParser:
    return GoParser.from_rules(rules)


PARSER_CATALOG: tuple[tuple[tuple[str, ...], ParserFactory], ...] = (
    ((".py", ".pyi", ".pyw"), _python_factory),
    ((".java",), _java_factory),
    ((".js", ".jsx", ".mjs", ".cjs"), _javascript_factory),
    ((".ts",), _typescript_factory),
    ((".tsx",), _tsx_factory),
    ((".go",), _go_factory),
)


def supported_parser_extensions() -> frozenset[str]:
    """Return every file extension handled by the parser catalog."""
    extensions: set[str] = set()
    for ext_group, _factory in PARSER_CATALOG:
        extensions.update(ext_group)
    return frozenset(extensions)


def build_production_parsers(rules: ParserRules | None = None) -> list[BaseParser]:
    """Instantiate all production Tree-sitter parsers using shared rules."""
    active_rules = rules or load_parser_rules()
    return [factory(active_rules) for _extensions, factory in PARSER_CATALOG]
