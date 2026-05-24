"""JavaScript Tree-sitter parser (US-03.04)."""

from __future__ import annotations

import tree_sitter_javascript as tsjs
from tree_sitter import Language

from drishti.ingestion.ast.ecmascript import EcmaScriptParser

_JAVASCRIPT_EXTENSIONS = (".js", ".jsx", ".mjs", ".cjs")
_QUERY_FILE = "javascript.scm"


class JavaScriptParser(EcmaScriptParser):
    """Extracts JavaScript classes, functions, and arrow functions."""

    @classmethod
    def from_package(cls) -> JavaScriptParser:
        """Build a parser using the packaged JavaScript query file."""
        language = Language(tsjs.language())
        return cls(language, cls.load_query(_QUERY_FILE), language_name="javascript")

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions handled by this parser."""
        return _JAVASCRIPT_EXTENSIONS
