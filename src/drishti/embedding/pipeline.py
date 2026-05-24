"""Chunk embedding pipeline combining dense and sparse vectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from drishti.embedding.dense import DenseEmbedder
from drishti.embedding.sparse import BM25SparseEncoder, EncodedSparseVector

if TYPE_CHECKING:
    from drishti.api.schemas import UniversalChunk


@dataclass(frozen=True)
class EmbeddedChunkVectors:
    """Dense and sparse vectors for a universal chunk."""

    chunk_id: str
    dense: list[float]
    sparse: EncodedSparseVector


class ChunkEmbeddingPipeline:
    """Embeds universal chunks for Qdrant hybrid indexing."""

    def __init__(
        self,
        dense_embedder: DenseEmbedder,
        *,
        sparse_encoder: BM25SparseEncoder | None = None,
    ) -> None:
        """Wire dense and optional sparse encoders."""
        self._dense = dense_embedder
        self._sparse = sparse_encoder or BM25SparseEncoder()

    @property
    def dense_dimensions(self) -> int:
        """Return dense vector size produced by the pipeline."""
        return self._dense.dimensions

    def embed_chunks(self, chunks: list[UniversalChunk]) -> list[EmbeddedChunkVectors]:
        """Return dense and sparse vectors aligned with input chunks."""
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]
        dense_vectors = self._dense.embed_texts(texts)
        sparse_vectors = self._sparse.encode_many(texts)

        return [
            EmbeddedChunkVectors(
                chunk_id=chunk.id,
                dense=dense,
                sparse=sparse,
            )
            for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors, strict=True)
        ]
