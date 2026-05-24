"""Map Qdrant scored points to ``SearchHit`` instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drishti.search.models import SearchHit

if TYPE_CHECKING:
    from qdrant_client.http.models.models import ScoredPoint


def point_to_search_hit(point: ScoredPoint, *, source: str) -> SearchHit:
    """Convert a Qdrant scored point into a ``SearchHit``."""
    payload = dict(point.payload or {})
    chunk_id = str(payload.get("chunk_id") or point.id)
    content = str(payload.get("content") or "")
    return SearchHit(
        chunk_id=chunk_id,
        score=float(point.score or 0.0),
        content=content,
        payload=payload,
        source=source,
    )
