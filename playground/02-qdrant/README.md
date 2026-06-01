# Module 02: Qdrant Vector Database Operations

Learn how Drishti uses Qdrant for hybrid vector search with dense and sparse vectors.

## What You'll Learn

1. Creating collections with named vectors (dense + sparse)
2. Upserting points with payloads
3. Filtering queries on metadata
4. Understanding hybrid search configuration

## Quick Start

```bash
# Start Qdrant
docker compose up -d qdrant

# Run the notebook
uv run jupyter notebook playground/02-qdrant/qdrant_demo.ipynb

# Or run the script
uv run python playground/02-qdrant/qdrant_demo.py
```

## Key Concepts

### Named Vectors

Qdrant supports multiple vectors per point. Drishti uses:
- `dense`: 1536-dim OpenAI embeddings for semantic search
- `sparse`: BM25 term vectors for keyword matching

### Payload Filtering

Each chunk has metadata that enables scoped searches:
```json
{
  "language": "python",
  "file_path": "src/auth/service.py",
  "content_type": "code",
  "node_type": "function_definition"
}
```
