"""BM25 sparse embedding encoder (US-05.02)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")


@dataclass(frozen=True)
class EncodedSparseVector:
    """Sparse vector components for Qdrant."""

    indices: list[int]
    values: list[float]


class BM25SparseEncoder:
    """Builds BM25-weighted sparse vectors over a fitted vocabulary."""

    def __init__(self, *, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize BM25 hyper-parameters."""
        self._k1 = k1
        self._b = b
        self._vocabulary: dict[str, int] = {}
        self._document_frequency: dict[int, int] = {}
        self._document_count = 0
        self._average_document_length = 0.0

    @property
    def vocabulary_size(self) -> int:
        """Return number of terms in the fitted vocabulary."""
        return len(self._vocabulary)

    def fit(self, documents: list[str]) -> None:
        """Fit IDF statistics from a corpus of document strings."""
        self._vocabulary.clear()
        self._document_frequency.clear()
        self._document_count = len(documents)
        if not documents:
            self._average_document_length = 0.0
            return

        total_length = 0
        for document in documents:
            tokens = self._tokenize(document)
            total_length += len(tokens)
            unique_indices: set[int] = set()
            for token in tokens:
                term_index = self._term_index(token)
                unique_indices.add(term_index)
            for term_index in unique_indices:
                self._document_frequency[term_index] = (
                    self._document_frequency.get(term_index, 0) + 1
                )

        self._average_document_length = total_length / self._document_count

    def encode(self, text: str) -> EncodedSparseVector:
        """Encode a single document into a sparse BM25 vector."""
        tokens = self._tokenize(text)
        if not tokens or self._document_count == 0:
            return EncodedSparseVector(indices=[], values=[])

        term_freq: dict[int, int] = {}
        for token in tokens:
            term_index = self._term_index(token)
            term_freq[term_index] = term_freq.get(term_index, 0) + 1

        doc_length = len(tokens)
        indices: list[int] = []
        values: list[float] = []
        for term_index, frequency in sorted(term_freq.items()):
            idf = self._idf(term_index)
            if idf <= 0:
                continue
            numerator = frequency * (self._k1 + 1)
            denominator = frequency + self._k1 * (
                1 - self._b + self._b * (doc_length / self._average_document_length)
            )
            weight = idf * (numerator / denominator)
            if weight > 0:
                indices.append(term_index)
                values.append(weight)

        return EncodedSparseVector(indices=indices, values=values)

    def encode_many(self, texts: list[str]) -> list[EncodedSparseVector]:
        """Fit on texts and return sparse vectors for each."""
        self.fit(texts)
        return [self.encode(text) for text in texts]

    def _term_index(self, token: str) -> int:
        if token not in self._vocabulary:
            self._vocabulary[token] = len(self._vocabulary)
        return self._vocabulary[token]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]

    def _idf(self, term_index: int) -> float:
        doc_freq = self._document_frequency.get(term_index, 0)
        if doc_freq == 0:
            return 0.0
        numerator = self._document_count - doc_freq + 0.5
        denominator = doc_freq + 0.5
        return math.log(1.0 + (numerator / denominator))
