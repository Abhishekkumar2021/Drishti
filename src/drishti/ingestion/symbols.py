"""Cross-file symbol resolution for ingestion (US-03.09)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from drishti.api.schemas import UniversalChunk


@dataclass
class SymbolTable:
    """Maps symbol names and context paths to defining file paths."""

    _by_name: dict[str, str] = field(default_factory=dict)
    _by_context_path: dict[str, str] = field(default_factory=dict)

    def register(self, chunk: UniversalChunk) -> None:
        """Index a chunk that defines a symbol in its file."""
        if not chunk.name:
            return
        self._by_name[chunk.name] = chunk.file_path
        if chunk.context_path:
            self._by_context_path[chunk.context_path] = chunk.file_path

    def register_many(self, chunks: list[UniversalChunk]) -> None:
        """Index all chunks from a single parse result."""
        for chunk in chunks:
            self.register(chunk)

    def resolve(self, symbol_name: str) -> str | None:
        """Return the file path where a simple symbol name is defined."""
        return self._by_name.get(symbol_name)

    def resolve_context(self, context_path: str) -> str | None:
        """Return the file path for a fully qualified context path."""
        return self._by_context_path.get(context_path)

    def definition_paths(self) -> frozenset[str]:
        """Return every file path that defines at least one indexed symbol."""
        return frozenset(self._by_name.values())
