# Module 03: Hybrid Search & RRF Fusion

Learn how Drishti combines dense and sparse search using Reciprocal Rank Fusion.

## What You'll Learn

1. Why hybrid search beats pure vector search
2. How BM25 (sparse) complements embeddings (dense)
3. Reciprocal Rank Fusion (RRF) algorithm
4. Re-ranking for final precision

## Quick Start

```bash
uv run python playground/03-hybrid-search/rrf_demo.py
```

## Key Concepts

### The Problem with Pure Vector Search

Dense embeddings capture semantic meaning but miss exact keywords:
- Query: "OAuth2 authentication"
- Dense search finds: "login system", "user verification"
- Misses: documents containing exactly "OAuth2"

### Hybrid Solution

| Search Type | Strengths | Weaknesses |
|-------------|-----------|------------|
| Dense (embeddings) | Semantic similarity | Misses exact terms |
| Sparse (BM25) | Exact keyword match | No semantic understanding |
| **Hybrid (RRF)** | Best of both | Requires tuning |

### RRF Formula

```
RRF_score(d) = Σ (1 / (k + rank_i(d)))
```

Where:
- `k` = 60 (dampening constant)
- `rank_i(d)` = rank of document d in list i
