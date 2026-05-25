"""Filesystem-backed workspaces for repos, uploads, and artifacts."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_WORKSPACE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,63}$")


@dataclass
class WorkspaceRecord:
    """Metadata for an isolated knowledge workspace."""

    id: str
    name: str
    created_at: str
    sources: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "sources": list(self.sources),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorkspaceRecord:
        return cls(
            id=str(payload["id"]),
            name=str(payload.get("name", payload["id"])),
            created_at=str(payload.get("created_at", "")),
            sources=[str(item) for item in payload.get("sources", [])],
            description=str(payload.get("description", "")),
        )


class WorkspaceStore:
    """Manage workspace directories under a configurable cache root."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._index_file = self._root / "workspaces.json"

    @classmethod
    def default(cls) -> WorkspaceStore:
        return cls(Path.home() / ".cache" / "drishti" / "workspaces")

    def create(self, *, name: str, description: str = "") -> WorkspaceRecord:
        workspace_id = str(uuid.uuid4())[:12]
        record = WorkspaceRecord(
            id=workspace_id,
            name=name.strip() or workspace_id,
            created_at=datetime.now(UTC).isoformat(),
            description=description.strip(),
        )
        self._workspace_dir(workspace_id).mkdir(parents=True, exist_ok=True)
        (self._workspace_dir(workspace_id) / "artifacts").mkdir(exist_ok=True)
        (self._workspace_dir(workspace_id) / "repos").mkdir(exist_ok=True)
        records = self.list_all()
        records.append(record)
        self._save_index(records)
        return record

    def get(self, workspace_id: str) -> WorkspaceRecord | None:
        self._validate_id(workspace_id)
        for record in self.list_all():
            if record.id == workspace_id:
                return record
        return None

    def list_all(self) -> list[WorkspaceRecord]:
        if not self._index_file.is_file():
            return []
        payload = json.loads(self._index_file.read_text(encoding="utf-8"))
        items = payload.get("workspaces", [])
        if not isinstance(items, list):
            return []
        return [WorkspaceRecord.from_dict(item) for item in items if isinstance(item, dict)]

    def root_path(self, workspace_id: str) -> Path:
        """Return workspace root (artifacts + linked repos)."""
        self._validate_id(workspace_id)
        path = self._workspace_dir(workspace_id)
        if not path.is_dir():
            msg = f"Unknown workspace: {workspace_id}"
            raise FileNotFoundError(msg)
        return path

    def artifacts_dir(self, workspace_id: str) -> Path:
        path = self.root_path(workspace_id) / "artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def ingest_root(self, workspace_id: str) -> Path:
        """Directory passed to the incremental indexer (git snapshot root)."""
        return self.root_path(workspace_id)

    def _workspace_dir(self, workspace_id: str) -> Path:
        return self._root / workspace_id

    def _save_index(self, records: list[WorkspaceRecord]) -> None:
        payload = {"workspaces": [record.to_dict() for record in records]}
        self._index_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _validate_id(workspace_id: str) -> None:
        if not _WORKSPACE_ID_RE.match(workspace_id):
            msg = "Invalid workspace id"
            raise ValueError(msg)
