"""JavaScript Tree-sitter parser (US-03.04)."""

from __future__ import annotations

import tree_sitter_javascript as tsjs
from tree_sitter import Language

from drishti.ingestion.ast.ecmascript import EcmaScriptParser
from drishti.ingestion.ast.rules import ParserRules, load_parser_rules

_JAVASCRIPT_EXTENSIONS = (".js", ".jsx", ".mjs", ".cjs")
_LANGUAGE = "javascript"


class JavaScriptParser(EcmaScriptParser):
    """Extracts JavaScript classes, functions, and arrow functions."""

    @classmethod
    def from_package(cls) -> JavaScriptParser:
        """Build a parser using the packaged JavaScript query file."""
        return cls.from_rules(load_parser_rules())

    @classmethod
    def from_rules(cls, rules: ParserRules) -> JavaScriptParser:
        """Build a parser using rule-driven query and thresholds."""
        language = Language(tsjs.language())
        return cls(
            language,
            cls.load_query(rules.query_file_for(_LANGUAGE)),
            language_name=_LANGUAGE,
            min_chunk_lines=rules.min_chunk_lines_for(_LANGUAGE),
        )

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions handled by this parser."""
        return _JAVASCRIPT_EXTENSIONS
