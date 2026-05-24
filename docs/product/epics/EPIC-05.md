# EPIC-05: Embedding & Vector Storage

This epic covers generating dense and sparse vector embeddings for chunks and indexing them in the Qdrant vector database.

---

## Epic Metadata
* **Complexity**: 34 Story Points
* **Priority**: P0 (Critical Blocker)
* **Status**: Planned

---

## User Stories

### US-05.01: OpenAI dense embedding integration
**As a** Drishti ML Engineer  
**I want** to generate dense vectors for chunks using OpenAI's `text-embedding-3-small` model  
**So that** we can capture semantic concepts across code and prose.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Client generates embeddings for text/code chunks.
2. [ ] Handles API rate limits, retries, and batch requests.
3. [ ] Embeddings generated are 1536-dimensional float arrays.

---

### US-05.02: Sparse embedding (BM25 tokenizer)
**As a** Retrieval Engineer  
**I want** to token-ize and index terms using BM25 algorithms  
**So that** exact symbol matches (like function names or type definitions) are retrievable.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Builds token frequencies for vocabulary.
2. [ ] Computes sparse vectors representing term importances.
3. [ ] Integrated directly into Qdrant sparse vectors collection.

---

### US-05.03: Qdrant database client initialization and index schemas
**As a** Database Administrator  
**I want** to initialize Qdrant collections with optimized vector and index structures  
**So that** queries are executed with sub-second response times.

**Complexity**: 13 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Establishes Qdrant collection configured with dense (1536 dims, cosine similarity) and sparse vector parameters.
2. [ ] Configures payload indexes for quick metadata filtering (by file path, language, content type).
3. [ ] Write integration test validating write/read cycles.

---

### US-05.04: Payload-based metadata filter compilation
**As a** Search API Developer  
**I want** to compile user filter queries into Qdrant payload filters  
**So that** users can restrict their searches to specific directories, file types, or classes.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Maps parameters like `language: python` or `file_path: src/auth/*` into valid Qdrant filter payloads.
2. [ ] Supports logical AND/OR operations on filters.
