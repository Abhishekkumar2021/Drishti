"""TypeScript and TSX Tree-sitter parsers (US-03.04)."""

from __future__ import annotations

import tree_sitter_typescript as tsts
from tree_sitter import Language

from drishti.ingestion.ast.ecmascript import EcmaScriptParser
from drishti.ingestion.ast.rules import ParserRules, load_parser_rules

_TYPESCRIPT_EXTENSIONS = (".ts",)
_TSX_EXTENSIONS = (".tsx",)
_LANGUAGE = "typescript"


class TypeScriptParser(EcmaScriptParser):
    """Extracts TypeScript interfaces, types, classes, and functions."""

    @classmethod
    def from_package(cls) -> TypeScriptParser:
        """Build a parser for ``.ts`` files."""
        return cls.from_rules(load_parser_rules())

    @classmethod
    def from_rules(cls, rules: ParserRules, *, tsx: bool = False) -> TypeScriptParser:
        """Build a parser using rule-driven query and thresholds."""
        language = Language(tsts.language_tsx() if tsx else tsts.language_typescript())
        return cls(
            language,
            cls.load_query(rules.query_file_for(_LANGUAGE)),
            language_name=_LANGUAGE,
            min_chunk_lines=rules.min_chunk_lines_for(_LANGUAGE),
        )

    @classmethod
    def for_tsx(cls, rules: ParserRules | None = None) -> TypeScriptParser:
        """Build a parser for ``.tsx`` files."""
        active_rules = rules or load_parser_rules()
        return cls.from_rules(active_rules, tsx=True)

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions handled by this parser instance."""
        return _TYPESCRIPT_EXTENSIONS

    @property
    def tsx_supported_extensions(self) -> tuple[str, ...]:
        """Extensions served by the TSX grammar instance."""
        return _TSX_EXTENSIONS
