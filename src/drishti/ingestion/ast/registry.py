"""Default parser registry wiring for ingestion."""

from __future__ import annotations

from drishti.ingestion.ast.python import PythonParser
from drishti.ingestion.base import ParserRegistry


def create_default_parser_registry() -> ParserRegistry:
    """Return a registry with all production parsers registered."""
    registry = ParserRegistry()
    python_parser = PythonParser.from_package()
    for extension in python_parser.supported_extensions:
        registry.register(extension, python_parser)
    return registry
