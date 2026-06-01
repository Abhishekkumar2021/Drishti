#!/usr/bin/env python3
"""Qdrant Vector Database Demo.

This script demonstrates Qdrant operations used in Drishti:
- Creating collections with named vectors
- Upserting points with payloads
- Filtering and searching

Run with: uv run python playground/02-qdrant/qdrant_demo.py
Requires: docker compose up -d qdrant
"""

from __future__ import annotations

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    NamedVector,
    PointStruct,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)


def main() -> None:
    """Run the Qdrant demo."""
    print("=" * 60)
    print("Qdrant Vector Database Demo")
    print("=" * 60)

    # Connect to Qdrant
    client = QdrantClient(host="localhost", port=6333)
    print("\n✅ Connected to Qdrant")

    collection_name = "demo_chunks"

    # 1. Create collection with named vectors
    print("\n1. CREATING COLLECTION")
    print("-" * 40)

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": VectorParams(
                size=384,  # Using smaller dims for demo
                distance=Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False),
            ),
        },
    )
    print(f"Created collection: {collection_name}")
    print("  - dense: 384-dim cosine similarity")
    print("  - sparse: BM25 term vectors")

    # 2. Insert sample points
    print("\n2. INSERTING POINTS")
    print("-" * 40)

    sample_chunks = [
        {
            "content": "def authenticate(username, password): ...",
            "language": "python",
            "file_path": "src/auth/service.py",
            "node_type": "function_definition",
            "name": "authenticate",
        },
        {
            "content": "class UserService: ...",
            "language": "python",
            "file_path": "src/users/service.py",
            "node_type": "class_definition",
            "name": "UserService",
        },
        {
            "content": "public void login(String user) { ... }",
            "language": "java",
            "file_path": "src/Auth.java",
            "node_type": "method_declaration",
            "name": "login",
        },
        {
            "content": "# Authentication Configuration\n\nAPI keys are stored...",
            "language": None,
            "file_path": "docs/auth.md",
            "node_type": None,
            "name": None,
        },
    ]

    points = []
    for i, chunk in enumerate(sample_chunks):
        # Generate fake embeddings (in real code, these come from OpenAI/Cohere)
        dense_vector = [0.1 * (i + 1)] * 384

        # Simple sparse vector (in real code, this is BM25 encoding)
        sparse_indices = [hash(word) % 1000 for word in chunk["content"].split()[:5]]
        sparse_values = [1.0] * len(sparse_indices)

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "dense": dense_vector,
                "sparse": SparseVector(indices=sparse_indices, values=sparse_values),
            },
            payload={
                "content": chunk["content"],
                "language": chunk["language"],
                "file_path": chunk["file_path"],
                "node_type": chunk["node_type"],
                "name": chunk["name"],
            },
        )
        points.append(point)
        print(f"  [{i+1}] {chunk['name'] or chunk['file_path']}")

    client.upsert(collection_name=collection_name, points=points)
    print(f"\n✅ Inserted {len(points)} points")

    # 3. Search with filter
    print("\n3. FILTERED SEARCH")
    print("-" * 40)

    # Search for Python functions only
    query_vector = [0.15] * 384  # Fake query embedding

    results = client.search(
        collection_name=collection_name,
        query_vector=NamedVector(name="dense", vector=query_vector),
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="language",
                    match=MatchValue(value="python"),
                ),
            ]
        ),
        limit=3,
        with_payload=True,
    )

    print("Query: 'authentication' (filtered to Python)")
    print(f"Results: {len(results)}")
    for r in results:
        print(f"  - {r.payload['name']} ({r.payload['file_path']})")
        print(f"    Score: {r.score:.4f}")

    # 4. Count with filter
    print("\n4. FILTERED COUNT")
    print("-" * 40)

    count = client.count(
        collection_name=collection_name,
        count_filter=Filter(
            must=[
                FieldCondition(
                    key="node_type",
                    match=MatchValue(value="function_definition"),
                ),
            ]
        ),
    )
    print(f"Functions indexed: {count.count}")

    # 5. Payload indexes
    print("\n5. PAYLOAD INDEXES")
    print("-" * 40)
    print("""
Drishti creates payload indexes for fast filtering:

  client.create_payload_index(
      collection_name="chunks",
      field_name="language",
      field_schema="keyword",  # Exact match
  )
  client.create_payload_index(
      collection_name="chunks",
      field_name="file_path",
      field_schema="text",  # Prefix/suffix match
  )
""")

    # Cleanup
    client.delete_collection(collection_name)
    print("\n✅ Demo complete (collection deleted)")


if __name__ == "__main__":
    main()
