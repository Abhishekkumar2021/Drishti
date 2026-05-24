"""Unit tests for Reciprocal Rank Fusion (US-06.03)."""

from __future__ import annotations

import pytest

from drishti.search.models import SearchHit
from drishti.search.rrf import ReciprocalRankFusion

pytestmark = pytest.mark.unit


def _hit(chunk_id: str, *, score: float = 1.0, source: str = "dense") -> SearchHit:
    return SearchHit(
        chunk_id=chunk_id,
        score=score,
        content=f"content-{chunk_id}",
        payload={"chunk_id": chunk_id},
        source=source,
    )


class TestReciprocalRankFusion:
    def test_merges_and_deduplicates_by_chunk_id(self) -> None:
        fusion = ReciprocalRankFusion(k=60)
        dense = [_hit("a"), _hit("b")]
        sparse = [_hit("b"), _hit("c")]

        merged = fusion.merge(dense, sparse)

        assert [hit.chunk_id for hit in merged] == ["b", "a", "c"]
        assert merged[0].source == "rrf"
        assert merged[0].score == pytest.approx((1 / 62) + (1 / 61))

    def test_rrf_formula_uses_configured_k(self) -> None:
        fusion = ReciprocalRankFusion(k=10)
        merged = fusion.merge([_hit("only")])

        assert merged[0].score == pytest.approx(1 / 11)
