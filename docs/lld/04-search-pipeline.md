# LLD Chapter 04: Hybrid Search Pipeline

This chapter details the design of Drishti's search and retrieval pipeline, focusing on query expansion, vector databases, Reciprocal Rank Fusion, and cross-encoder re-ranking.

---

## Table of Contents

1. [Retrieval Pipeline Overview](#1-retrieval-pipeline-overview)
2. [Query Expansion Strategy](#2-query-expansion-strategy)
3. [Vector retrieval: Dense & Sparse Search](#3-vector-retrieval-dense--sparse-search)
4. [Reciprocal Rank Fusion (RRF) Algorithm](#4-reciprocal-rank-fusion-rrf-algorithm)
5. [Cohere Cross-Encoder Re-ranking](#5-cohere-cross-encoder-re-ranking)
6. [Code Implementation Blueprint](#6-code-implementation-blueprint)

---

## 1. Retrieval Pipeline Overview

Retrieval is structured as a multi-stage funnel designed to maximize recall in the first stage and precision in the final stages.

```
       [User Query: "auth token"]
                   │
                   ▼
       ┌───────────────────────┐
       │ 1. Query Expansion    │ ──▶ ["JWT", "verify", "bearer", "cookie"]
       └───────────┬───────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
 ┌──────────────┐    ┌──────────────┐
 │ 2. Dense     │    │ 2. Sparse    │
 │    Retriever │    │    Retriever │
 └───────┬──────┘    └───────┬──────┘
         │                   │
         └─────────┬─────────┘
                   ▼
       ┌───────────────────────┐
       │ 3. Reciprocal Rank    │
       │    Fusion (RRF)       │
       └───────────┬───────────┘
                   │
                   ▼
       ┌───────────────────────┐
       │ 4. Cohere Reranker    │
       └───────────┬───────────┘
                   │
                   ▼
       ┌───────────────────────┐
       │ 5. Context Builder    │ ──▶ Prompt context for Claude
       └───────────────────────┘
```

---

## 2. Query Expansion Strategy

To handle naming inconsistencies across different codebases, the query is expanded using an LLM.

### Expansion Prompt
```
You are a software search utility. Expand the user query with alternative terminology.
Output a flat JSON list of strings containing:
1. Exact class or method names that map to the concept.
2. Common API terminology, variables, or exception names.

Query: "rate limit"
Response: ["RateLimiter", "throttle", "TokenBucket", "too_many_requests", "RequestThrottler", "429"]
```

---

## 3. Vector retrieval: Dense & Sparse Search

Both retrievers query the Qdrant `drishti_chunks` collection in parallel:

* **Dense Search**: Generates a 1536-dimensional float vector for the query and runs a Cosine similarity search. This targets semantic intent.
* **Sparse Search**: Generates sparse vectors mapping term weights (BM25 vocabulary indexes) for the query. This targets exact matching symbols, variables, or functions.

Both retrieval pipelines return up to 50 results each, including metadata and relevance scores.

---

## 4. Reciprocal Rank Fusion (RRF) Algorithm

RRF resolves differences between dense similarity scores (cosine similarity floats) and sparse keyword scores (BM25 indexes).

### Mathematical Definition
For each document $d$ in the union of retrievals $D$:

$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

* $M$: The set of retrievers (Dense and Sparse).
* $r_m(d)$: The position (rank index, 1-indexed) of document $d$ in the results of retriever $m$. If the document is not returned by a retriever, $r_m(d)$ is set to $\infty$.
* $k$: Smoothing constant (default: 60) to prevent top-ranked documents from completely dominating the score.

---

## 5. Cohere Cross-Encoder Re-ranking

 RRF yields an merged candidate list, which is then re-ranked. We use a **Cross-Encoder Model** (Cohere Rerank v3.5).
* **Bi-Encoder (Dense Search)**: Embeds the query and the documents independently, calculating similarity via dot product. It is fast but cannot model deep cross-token correlations.
* **Cross-Encoder (Reranker)**: Inputs the query and document text together into the model attention layers. This calculates deep, sentence-level interactions, improving relevance scoring.

The top 10 re-ranked documents are selected for the LLM prompt context.

---

## 6. Code Implementation Blueprint

The following classes implement the RRF fusion and Cohere re-ranking logic:

```python
from typing import List, Dict, Any

class ReciprocalRankFusion:
    """
    RRF merger for combining dense and sparse search lists.
    """
    def __init__(self, k: int = 60):
        self.k = k
        
    def merge(self, dense_results: List[Dict[str, Any]], sparse_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merges results and returns a ranked list.
        """
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}
        
        # Helper to compute rank scores
        def accum_scores(results: List[Dict[str, Any]]) -> None:
            for rank, doc in enumerate(results, start=1):
                doc_id = doc["chunk_id"]
                doc_map[doc_id] = doc
                
                if doc_id not in scores:
                    scores[doc_id] = 0.0
                scores[doc_id] += 1.0 / (self.k + rank)
                
        accum_scores(dense_results)
        accum_scores(sparse_results)
        
        # Sort documents based on aggregated RRF scores
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        merged_results = []
        for doc_id in sorted_ids:
            doc = doc_map[doc_id]
            doc["rrf_score"] = scores[doc_id]
            merged_results.append(doc)
            
        return merged_results

class CohereReranker:
    """
    Reranker wrapper executing cross-encoder evaluation.
    """
    def __init__(self, api_key: str, model: str = "rerank-english-v3.0"):
        import cohere
        self.client = cohere.Client(api_key=api_key)
        self.model = model
        
    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Re-ranks candidates and returns the top N.
        """
        if not candidates:
            return []
            
        documents = [c["content"] for c in candidates]
        
        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_n
        )
        
        reranked_results = []
        for result in response.results:
            idx = result.index
            candidate = candidates[idx].copy()
            candidate["rerank_score"] = result.relevance_score
            reranked_results.append(candidate)
            
        return reranked_results
```
