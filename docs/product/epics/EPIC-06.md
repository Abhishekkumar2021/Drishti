# EPIC-06: Hybrid Search Engine

This epic covers building the retrieval engine that merges keyword and semantic matches, re-ranks results, and expands user queries.

---

## Epic Metadata
* **Complexity**: 55 Story Points
* **Priority**: P0 (Critical Blocker)
* **Status**: Planned

---

## User Stories

### US-06.01: Dense vector retriever
**As a** Drishti Retrieval Pipeline  
**I want** to search the vector database using dense query embeddings  
**So that** I can retrieve chunks that are semantically related to the user query.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Embeds the incoming user query.
2. [ ] Performs a k-nearest neighbor (k-NN) search against the Qdrant dense collection.
3. [ ] Returns top K candidate chunks with their cosine similarity scores.

---

### US-06.02: Sparse BM25 retriever
**As a** Drishti Retrieval Pipeline  
**I want** to search the vector database using sparse query vectors  
**So that** I can retrieve exact matching code tokens or keywords.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Converts queries into sparse term vectors.
2. [ ] Executes a sparse vector search in Qdrant.
3. [ ] Returns top K candidates with matching BM25 keyword scores.

---

### US-06.03: Reciprocal Rank Fusion (RRF) combiner
**As a** Retrieval Architect  
**I want** to combine dense and sparse results using Reciprocal Rank Fusion  
**So that** the final ranking benefits from both keyword precision and semantic meaning.

**Complexity**: 13 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Implements the RRF formula: `score = sum(1 / (60 + rank_i))`.
2. [ ] Merges and de-duplicates documents retrieved from both dense and sparse sources.
3. [ ] Returns a single unified list ranked by RRF score.

---

### US-06.04: Cohere re-ranking integration
**As a** Search Developer  
**I want** to pass the top RRF candidates through Cohere's rerank v3 endpoint  
**So that** the most relevant context blocks are placed at the top of the LLM context.

**Complexity**: 13 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Sends candidates to Cohere rerank API.
2. [ ] Re-orders chunks based on cross-encoder relevance scores.
3. [ ] Filters out chunks below a minimum relevance threshold.

---

### US-06.05: LLM query expansion implementation
**As a** Power User  
**I want** my query to be expanded into synonymous technical terms  
**So that** search finds matching code regardless of exact variable naming.

**Complexity**: 13 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Uses a fast LLM prompt to generate technical synonyms (e.g. `auth` → `token`, `sign_in`, `authenticate`).
2. [ ] Combines original query and expanded terms in the retrieval request.
