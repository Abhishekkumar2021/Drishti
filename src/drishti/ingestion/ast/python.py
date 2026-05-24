"""Python Tree-sitter parser (US-03.02)."""

from __future__ import annotations

import tree_sitter_python as tspython
from tree_sitter import Language

from drishti.ingestion.ast.base import TreeSitterParser

_PYTHON_EXTENSIONS = (".py", ".pyi", ".pyw")


class PythonParser(TreeSitterParser):
    """Extracts Python classes and functions into universal chunks."""

    @classmethod
    def from_package(cls) -> PythonParser:
        """Build a parser using the packaged Python query file."""
        query_scm, _query_path = cls.load_query("python.scm")
        language = Language(tspython.language())
        return cls(language, query_scm, language_name="python")

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions handled by this parser."""
        return _PYTHON_EXTENSIONS
