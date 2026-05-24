"""Default parser registry wiring for ingestion."""

from __future__ import annotations

from functools import lru_cache

from drishti.ingestion.ast.python import PythonParser
from drishti.ingestion.base import ParserRegistry


@lru_cache(maxsize=1)
def _python_parser() -> PythonParser:
    return PythonParser.from_package()


def create_default_parser_registry() -> ParserRegistry:
    """Return a registry with all production parsers registered."""
    registry = ParserRegistry()
    python_parser = _python_parser()
    for extension in python_parser.supported_extensions:
        registry.register(extension, python_parser)
    return registry
