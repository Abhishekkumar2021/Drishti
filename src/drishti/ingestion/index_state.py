"""Persistent index state for incremental git-based indexing (US-03.10)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class IndexState:
    """Tracks the last indexed commit and per-file content hashes."""

    indexed_commit: str
    files: dict[str, str] = field(default_factory=dict)
    version: int = 1


class IndexStateStore:
    """Reads and writes index state as JSON under the repository."""

    def __init__(self, state_file: Path) -> None:
        """Initialize the store at the given JSON file path."""
        self._state_file = state_file

    @classmethod
    def for_repository(cls, repo_root: Path) -> IndexStateStore:
        """Return the default state store path for a repository root."""
        return cls(repo_root / ".drishti" / "index-state.json")

    def load(self) -> IndexState | None:
        """Load index state or return None when no prior index exists."""
        if not self._state_file.is_file():
            return None
        payload: dict[str, Any] = json.loads(self._state_file.read_text(encoding="utf-8"))
        files = payload.get("files", {})
        indexed_commit = payload.get("indexed_commit")
        if not isinstance(indexed_commit, str):
            return None
        file_map = {
            str(path): str(digest) for path, digest in files.items() if isinstance(digest, str)
        }
        return IndexState(
            indexed_commit=indexed_commit,
            files=file_map,
            version=int(payload.get("version", 1)),
        )

    def save(self, state: IndexState) -> None:
        """Persist index state to disk."""
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": state.version,
            "indexed_commit": state.indexed_commit,
            "files": dict(sorted(state.files.items())),
        }
        self._state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def clear(self) -> None:
        """Remove persisted index state."""
        if self._state_file.is_file():
            self._state_file.unlink()
