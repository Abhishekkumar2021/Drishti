"""Default parser registry wiring for ingestion."""

from __future__ import annotations

from functools import lru_cache

from drishti.ingestion.ast.catalog import PARSER_CATALOG
from drishti.ingestion.ast.rules import ParserRules, load_parser_rules
from drishti.ingestion.base import ParserRegistry


@lru_cache(maxsize=1)
def _parser_rules() -> ParserRules:
    return load_parser_rules()


def create_default_parser_registry() -> ParserRegistry:
    """Return a registry with all production Tree-sitter parsers registered."""
    registry = ParserRegistry()
    for extensions, factory in PARSER_CATALOG:
        parser = factory(_parser_rules())
        for extension in extensions:
            registry.register(extension, parser)
    return registry
