"""Python Tree-sitter parser (US-03.02)."""

from __future__ import annotations

import tree_sitter_python as tspython
from tree_sitter import Language

from drishti.ingestion.ast.base import TreeSitterParser
from drishti.ingestion.ast.rules import ParserRules, load_parser_rules

_PYTHON_EXTENSIONS = (".py", ".pyi", ".pyw")
_LANGUAGE = "python"


class PythonParser(TreeSitterParser):
    """Extracts Python classes and functions into universal chunks."""

    @classmethod
    def from_package(cls) -> PythonParser:
        """Build a parser using the packaged Python query file."""
        return cls.from_rules(load_parser_rules())

    @classmethod
    def from_rules(cls, rules: ParserRules) -> PythonParser:
        """Build a parser using rule-driven query and thresholds."""
        language = Language(tspython.language())
        return cls(
            language,
            cls.load_query(rules.query_file_for(_LANGUAGE)),
            language_name=_LANGUAGE,
            min_chunk_lines=rules.min_chunk_lines_for(_LANGUAGE),
        )

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions handled by this parser."""
        return _PYTHON_EXTENSIONS
