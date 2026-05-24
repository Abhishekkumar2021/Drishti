"""Default parser registry wiring for ingestion."""

from __future__ import annotations

from functools import lru_cache

from drishti.ingestion.ast.java import JavaParser
from drishti.ingestion.ast.javascript import JavaScriptParser
from drishti.ingestion.ast.python import PythonParser
from drishti.ingestion.ast.typescript import TypeScriptParser
from drishti.ingestion.base import BaseParser, ParserRegistry


@lru_cache(maxsize=1)
def _python_parser() -> PythonParser:
    return PythonParser.from_package()


@lru_cache(maxsize=1)
def _java_parser() -> JavaParser:
    return JavaParser.from_package()


@lru_cache(maxsize=1)
def _javascript_parser() -> JavaScriptParser:
    return JavaScriptParser.from_package()


@lru_cache(maxsize=1)
def _typescript_parser() -> TypeScriptParser:
    return TypeScriptParser.from_package()


@lru_cache(maxsize=1)
def _tsx_parser() -> TypeScriptParser:
    return TypeScriptParser.for_tsx()


def _register_parser(registry: ParserRegistry, parser: BaseParser) -> None:
    extensions = getattr(parser, "supported_extensions", None)
    if extensions is None:
        msg = f"Parser {type(parser).__name__} does not expose supported_extensions"
        raise TypeError(msg)
    for extension in extensions:
        registry.register(extension, parser)


def create_default_parser_registry() -> ParserRegistry:
    """Return a registry with all production parsers registered."""
    registry = ParserRegistry()
    for parser in (
        _python_parser(),
        _java_parser(),
        _javascript_parser(),
        _typescript_parser(),
    ):
        _register_parser(registry, parser)

    for extension in _tsx_parser().tsx_supported_extensions:
        registry.register(extension, _tsx_parser())

    return registry
