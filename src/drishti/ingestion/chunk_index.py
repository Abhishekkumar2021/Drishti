"""Chunk index storage abstraction for ingestion (US-03.10)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from drishti.api.schemas import UniversalChunk


class ChunkIndex(ABC):
    """Abstract index of universal chunks keyed by file path."""

    @abstractmethod
    def upsert(self, chunks: list[UniversalChunk]) -> int:
        """Insert or replace chunks; return number of chunks stored."""

    @abstractmethod
    def delete_by_file_paths(self, file_paths: Iterable[str]) -> int:
        """Remove all chunks for the given relative file paths; return count removed."""

    @abstractmethod
    def count(self) -> int:
        """Return total number of indexed chunks."""


class InMemoryChunkIndex(ChunkIndex):
    """In-memory chunk index used in tests and local pipelines before Qdrant (EPIC-05)."""

    def __init__(self) -> None:
        """Initialize an empty in-memory chunk index."""
        self._chunks: dict[str, UniversalChunk] = {}
        self._paths: dict[str, set[str]] = {}

    def upsert(self, chunks: list[UniversalChunk]) -> int:
        """Insert or replace chunks; return number of chunks stored."""
        for chunk in chunks:
            previous = self._chunks.get(chunk.id)
            if previous is not None:
                self._paths[previous.file_path].discard(previous.id)
            self._chunks[chunk.id] = chunk
            self._paths.setdefault(chunk.file_path, set()).add(chunk.id)
        return len(chunks)

    def delete_by_file_paths(self, file_paths: Iterable[str]) -> int:
        """Remove all chunks for the given relative file paths; return count removed."""
        removed = 0
        for file_path in file_paths:
            chunk_ids = self._paths.pop(file_path, set())
            for chunk_id in chunk_ids:
                self._chunks.pop(chunk_id, None)
                removed += 1
        return removed

    def count(self) -> int:
        """Return total number of indexed chunks."""
        return len(self._chunks)

    def clear(self) -> None:
        """Remove every indexed chunk."""
        self._chunks.clear()
        self._paths.clear()

    def indexed_file_paths(self) -> frozenset[str]:
        """Return file paths that currently have chunks."""
        return frozenset(self._paths)

    def chunks_for_path(self, file_path: str) -> list[UniversalChunk]:
        """Return chunks for a file path (test helper)."""
        ids = self._paths.get(file_path, set())
        return [self._chunks[chunk_id] for chunk_id in ids if chunk_id in self._chunks]
