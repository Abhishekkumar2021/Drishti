# 03. Hybrid Search Mechanics: RRF & Re-ranking

---

## Table of Contents

1. [Why Building Drishti Is Hard](#1-why-building-drishti-is-hard)
2. [Core Theory: Reciprocal Rank Fusion (RRF)](#2-core-theory-reciprocal-rank-fusion-rrf)
3. [Inside Rerankers: Bi-Encoders vs. Cross-Encoders](#3-inside-rerankers-bi-encoders-vs-cross-encoders)
4. [Query Expansion & LLM Routing](#4-query-expansion-llm-routing)
5. [Drishti's Search Engine Implementation](#5-drishtis-search-engine-implementation)
6. [How Senior Interviewers Test This](#6-how-senior-interviewers-test-this)
7. [Key Takeaways & What's Next](#7-key-takeaways--whats-next)

---

## 1. Why Building Drishti Is Hard

Retrieving code chunks requires merging two separate score sheets:
* **Dense Search** returns cosine similarity values between `0.0` and `1.0`.
* **Sparse Search** returns BM25 scores which are unbounded floats (often ranging between `0.0` and `30.0` depending on terms frequencies).

Directly adding or multiplying these scores leads to distortions: the unbounded BM25 scores overwhelm the dense cosine values, rendering the dense search signal useless.

To resolve this, Drishti uses **Reciprocal Rank Fusion (RRF)**, which normalizes scores based on document ranks rather than raw similarity values, and passes the merged results to a **Cross-Encoder re-ranker**.

---

## 2. Core Theory: Reciprocal Rank Fusion (RRF)

RRF is a rank-aggregation algorithm that combines the outputs of multiple retrievers without needing to normalize their raw scores.

### The RRF Formula
The score for a document $d \in D$ is calculated as:

$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

* $M$: The set of retrieval runs (Dense and Sparse).
* $r_m(d)$: The rank position of document $d$ in the output of retriever $m$ (1-indexed). If a document is not returned, its rank is set to $\infty$, making its contribution $0$.
* $k$: A smoothing constant (usually set to $60$) that prevents top-ranked documents from overly dominating the final score.

RRF guarantees that a document appearing at rank 1 in one retriever and rank 100 in another will be scored higher than a document that is ranked moderately low in both.

---

## 3. Inside Rerankers: Bi-Encoders vs. Cross-Encoders

To understand re-ranking, we must contrast two architectures:

```
BI-ENCODER (First-Stage Retrieval)
Query ──▶ [Embedding Model] ──▶ Vector ──┐
                                         ├─► Cosine Similarity (Fast)
Chunk ──▶ [Embedding Model] ──▶ Vector ──┘

CROSS-ENCODER (Second-Stage Re-ranking)
Query ─┐
       ├─▶ [Transformer Attention Layers] ─► Relevance Score (Highly Accurate)
Chunk ─┘
```

* **Bi-Encoders**: Embed queries and documents independently. Searching is fast because we calculate simple dot products, but the model cannot capture cross-token relationships.
* **Cross-Encoders**: Input the query and document text together into the transformer attention layers. This allows the model to capture deep semantic interactions, producing highly accurate relevance scores.

---

## 4. Query Expansion & LLM Routing

To resolve vocabulary mismatch (e.g. searching for "auth" when the code uses "login"), the query is expanded prior to retrieval:
1. The user query is passed to a fast LLM.
2. The LLM returns a list of technical synonyms and variable name variations.
3. These terms are appended to the search query, increasing the likelihood of retrieval matches.

---

## 5. Drishti's Search Engine Implementation

Drishti implements this multi-stage retrieval pipeline:
1. **Parallel Search**: The query and its expansions are submitted to Qdrant's dense and sparse vector engines.
2. **Rank Aggregation**: RRF combines the top 50 dense and top 50 sparse results into a single list.
3. **Cross-Encoder Filtering**: The top 50 merged candidates are sent to the Cohere Rerank API, which returns the top 10 most relevant chunks.

---

## 6. How Senior Interviewers Test This

**"Why use RRF over simple score normalization (like min-max scaling)?"**
> Min-max scaling relies on the minimum and maximum scores of a single query run. These values fluctuate depending on query length, vocabulary size, and the retrieved candidate pool. This makes min-max scaling unstable across different queries. RRF is score-agnostic, using only document ranks, which ensures stable and consistent aggregation.

**"What is the function of the constant $k$ in the RRF formula?"**
> The constant $k$ (typically set to 60) acts as a smoothing factor. Without $k$ (i.e. if $k=0$), a document ranked 1st would receive a score of $1.0$, while a document ranked 2nd would receive $0.5$. This steep drop-off allows a single rank-1 result to completely dominate the scoring. Setting $k=60$ flattens the curve, ensuring that documents with consistent mid-tier rankings across both retrievers can compete with a single outlier rank-1 result.

---

## 7. Key Takeaways & What's Next

1. **RRF merges dense and sparse results** using document ranks rather than raw scores.
2. **Bi-encoders are optimized for speed**, while **Cross-encoders are optimized for accuracy**.
3. **Drishti uses Cohere Rerank** as a second-stage cross-encoder step.

**Next → [04. PDF Layout Analysis](04-pdf-layout-analysis.md):** Learn how layout-aware parsers extract structured text, headers, and tables from PDFs.
