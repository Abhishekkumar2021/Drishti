"""Search result models for hybrid retrieval."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class SearchHit:
    """A retrieved chunk candidate with score and metadata."""

    chunk_id: str
    score: float
    content: str
    payload: dict[str, Any]
    source: str

    def with_score(self, score: float, *, source: str) -> SearchHit:
        """Return a copy with an updated score and source label."""
        return replace(self, score=score, source=source)
