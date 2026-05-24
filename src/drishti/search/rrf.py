"""Reciprocal Rank Fusion combiner (US-06.03)."""

from __future__ import annotations

from drishti.search.models import SearchHit


class ReciprocalRankFusion:
    """Merge dense and sparse ranked lists using RRF."""

    def __init__(self, *, k: int = 60) -> None:
        """Initialize smoothing constant ``k`` (default 60)."""
        self._k = max(1, k)

    def merge(self, *result_lists: list[SearchHit]) -> list[SearchHit]:
        """Fuse ranked lists, de-duplicate by ``chunk_id``, and sort by RRF score."""
        scores: dict[str, float] = {}
        doc_map: dict[str, SearchHit] = {}

        for results in result_lists:
            for rank, hit in enumerate(results, start=1):
                doc_map[hit.chunk_id] = hit
                scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + (1.0 / (self._k + rank))

        sorted_ids = sorted(scores, key=scores.__getitem__, reverse=True)
        return [
            doc_map[chunk_id].with_score(scores[chunk_id], source="rrf") for chunk_id in sorted_ids
        ]
