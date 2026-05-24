"""Incremental repository indexing via git diffs (US-03.10)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from drishti.ingestion.base import ParserRegistry

if TYPE_CHECKING:
    from drishti.api.schemas import UniversalChunk
from drishti.ingestion.chunk_index import ChunkIndex, InMemoryChunkIndex
from drishti.ingestion.git_changes import (
    discover_parseable_files,
    file_content_hash,
    filter_existing_paths,
    resolve_changes,
)
from drishti.ingestion.index_state import IndexState, IndexStateStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IncrementalIndexResult:
    """Summary of an incremental indexing run."""

    head_commit: str
    base_commit: str | None
    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]
    chunks_indexed: int
    chunks_removed: int
    files_parsed: int


class IncrementalIndexer:
    """Indexes only git-changed files and purges deleted paths from the chunk index."""

    def __init__(
        self,
        repo_root: Path,
        *,
        parser_registry: ParserRegistry,
        chunk_index: ChunkIndex,
        state_store: IndexStateStore | None = None,
    ) -> None:
        """Wire the indexer to a repository root and storage backends."""
        self._repo_root = repo_root.resolve()
        self._parser_registry = parser_registry
        self._chunk_index = chunk_index
        self._state_store = state_store or IndexStateStore.for_repository(self._repo_root)

    def run(self, *, force_full: bool = False) -> IncrementalIndexResult:
        """Run incremental indexing from stored state to HEAD."""
        parseable = discover_parseable_files(self._repo_root, parser_registry=self._parser_registry)
        prior_state = None if force_full else self._state_store.load()

        if force_full:
            if hasattr(self._chunk_index, "clear"):
                self._chunk_index.clear()
            else:
                paths = set(parseable)
                if isinstance(self._chunk_index, InMemoryChunkIndex):
                    paths |= self._chunk_index.indexed_file_paths()
                self._chunk_index.delete_by_file_paths(paths)
            self._state_store.clear()

        indexed_commit = None if prior_state is None else prior_state.indexed_commit
        tracked_paths = parseable
        if prior_state is not None:
            tracked_paths = frozenset(parseable | set(prior_state.files))
        changes = resolve_changes(
            self._repo_root,
            indexed_commit=indexed_commit,
            parseable_paths=tracked_paths,
        )

        removed = 0
        if changes.deleted:
            removed = self._chunk_index.delete_by_file_paths(changes.deleted)

        paths_to_parse = filter_existing_paths(
            self._repo_root,
            (*changes.added, *changes.modified),
        )
        if changes.modified:
            removed += self._chunk_index.delete_by_file_paths(changes.modified)

        all_chunks: list[UniversalChunk] = []
        file_hashes: dict[str, str] = {} if prior_state is None else dict(prior_state.files)

        for relative_path in paths_to_parse:
            chunks = self._parse_file(relative_path)
            all_chunks.extend(chunks)
            absolute = self._repo_root / relative_path
            file_hashes[relative_path] = file_content_hash(absolute)

        for deleted_path in changes.deleted:
            file_hashes.pop(deleted_path, None)

        indexed_count = 0
        if all_chunks:
            indexed_count = self._chunk_index.upsert(all_chunks)

        new_state = IndexState(
            indexed_commit=changes.head_commit,
            files=file_hashes,
        )
        self._state_store.save(new_state)

        logger.info(
            "Incremental index complete commit=%s added=%d modified=%d deleted=%d chunks=%d",
            changes.head_commit[:8],
            len(changes.added),
            len(changes.modified),
            len(changes.deleted),
            indexed_count,
        )

        return IncrementalIndexResult(
            head_commit=changes.head_commit,
            base_commit=changes.base_commit,
            added=changes.added,
            modified=changes.modified,
            deleted=changes.deleted,
            chunks_indexed=indexed_count,
            chunks_removed=removed,
            files_parsed=len(paths_to_parse),
        )

    def _parse_file(self, relative_path: str) -> list[UniversalChunk]:
        absolute = self._repo_root / relative_path
        parser = self._parser_registry.get_parser(relative_path)
        content = absolute.read_bytes()
        modified = datetime.fromtimestamp(absolute.stat().st_mtime, tz=UTC)
        return parser.parse(content, relative_path, last_modified=modified)
