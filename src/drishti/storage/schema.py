"""Qdrant collection schema helpers (US-05.03)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qdrant_client.models import (
    Distance,
    PayloadSchemaType,
    SparseVectorParams,
    VectorParams,
)

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"

PAYLOAD_INDEX_FIELDS: dict[str, PayloadSchemaType] = {
    "language": PayloadSchemaType.KEYWORD,
    "content_type": PayloadSchemaType.KEYWORD,
    "source_type": PayloadSchemaType.KEYWORD,
    "file_path": PayloadSchemaType.KEYWORD,
    "node_type": PayloadSchemaType.KEYWORD,
    "name": PayloadSchemaType.KEYWORD,
    "parent_class": PayloadSchemaType.KEYWORD,
    "package_name": PayloadSchemaType.KEYWORD,
}


def ensure_chunk_collection(
    client: QdrantClient,
    *,
    collection_name: str,
    dense_dimensions: int,
    recreate: bool = False,
) -> None:
    """Create the hybrid chunk collection and payload indexes if missing."""
    if recreate and client.collection_exists(collection_name):
        client.delete_collection(collection_name=collection_name)

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                DENSE_VECTOR_NAME: VectorParams(
                    size=dense_dimensions,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                SPARSE_VECTOR_NAME: SparseVectorParams(),
            },
        )

    for field_name, schema_type in PAYLOAD_INDEX_FIELDS.items():
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=schema_type,
        )
