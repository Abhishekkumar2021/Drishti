"""Unit tests for BM25 sparse embeddings (US-05.02)."""

from __future__ import annotations

import pytest

from drishti.embedding.sparse import BM25SparseEncoder

pytestmark = pytest.mark.unit


class TestBM25SparseEncoder:
    def test_fit_builds_vocabulary(self) -> None:
        encoder = BM25SparseEncoder()
        encoder.fit(["AuthService validate token", "TokenValidator interface"])
        assert encoder.vocabulary_size > 0

    def test_encode_returns_indices_and_values(self) -> None:
        encoder = BM25SparseEncoder()
        vectors = encoder.encode_many(
            [
                "class AuthService:\n    def validate(self, token: str) -> bool:",
                "def validate(token: str) -> bool:",
            ]
        )
        assert len(vectors) == 2
        assert vectors[0].indices
        assert len(vectors[0].indices) == len(vectors[0].values)
        assert all(value > 0 for value in vectors[0].values)

    def test_empty_document_returns_empty_sparse_vector(self) -> None:
        encoder = BM25SparseEncoder()
        encoder.fit(["alpha beta"])
        vector = encoder.encode("")
        assert vector.indices == []
        assert vector.values == []
