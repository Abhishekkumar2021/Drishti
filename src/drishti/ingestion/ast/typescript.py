"""TypeScript and TSX Tree-sitter parsers (US-03.04)."""

from __future__ import annotations

import tree_sitter_typescript as tsts
from tree_sitter import Language

from drishti.ingestion.ast.ecmascript import EcmaScriptParser

_TYPESCRIPT_EXTENSIONS = (".ts",)
_TSX_EXTENSIONS = (".tsx",)
_QUERY_FILE = "typescript.scm"


class TypeScriptParser(EcmaScriptParser):
    """Extracts TypeScript interfaces, types, classes, and functions."""

    @classmethod
    def from_package(cls) -> TypeScriptParser:
        """Build a parser for ``.ts`` files."""
        language = Language(tsts.language_typescript())
        return cls(language, cls.load_query(_QUERY_FILE), language_name="typescript")

    @classmethod
    def for_tsx(cls) -> TypeScriptParser:
        """Build a parser for ``.tsx`` files."""
        language = Language(tsts.language_tsx())
        return cls(language, cls.load_query(_QUERY_FILE), language_name="typescript")

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions handled by this parser instance."""
        return _TYPESCRIPT_EXTENSIONS

    @property
    def tsx_supported_extensions(self) -> tuple[str, ...]:
        """Extensions served by the TSX grammar instance."""
        return _TSX_EXTENSIONS
