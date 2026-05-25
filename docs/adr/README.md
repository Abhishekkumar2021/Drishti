# Architecture Decision Records (ADRs): Drishti (दृष्टि)

This directory contains the immutable Architecture Decision Records (ADRs) documenting the technology stack choices and design patterns chosen for Drishti.

---

## What is an ADR?

An Architecture Decision Record (ADR) is a short document that captures a significant design or technology decision, along with its context and consequences. It is stored in the repository to act as a historical log for future maintainers.

### ADR Status Lifecycle
* **Proposed**: The decision is currently under review or discussion (via RFC).
* **Approved**: The decision has been agreed upon and is being implemented.
* **Superseded**: A subsequent decision has replaced this record.

---

## ADR Index

| ADR ID | Decision Title | Status | Impact Area |
|--------|----------------|--------|-------------|
| **[ADR-001](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-001-fastapi-backend-framework.md)** | FastAPI backend framework | 🟩 Approved | API & Runtime |
| **[ADR-002](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-002-tree-sitter-ast-parsing.md)** | Tree-sitter AST parsing | 🟩 Approved | Ingestion Engine |
| **[ADR-003](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-003-openai-text-embedding-3-small.md)** | OpenAI text-embedding-3-small | 🟩 Approved | Embeddings |
| **[ADR-004](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-004-qdrant-vector-database.md)** | Qdrant vector database | 🟩 Approved | Vector Storage |
| **[ADR-005](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-005-cohere-reranker.md)** | Cohere re-ranking engine | 🟩 Approved | Retrieval Quality |
| **[ADR-006](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-006-claude-api-generation.md)** | Claude API for text/visual parsing | 🟩 Approved | LLM Generation |
| **[ADR-007](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-007-pymupdf-pdf-parsing.md)** | PyMuPDF for PDF layout parsing | 🟩 Approved | Ingestion Engine |
| **[ADR-008](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-008-neo4j-dependency-graph.md)** | Neo4j dependency graph storage | 🟩 Approved | Relationship Engine |
| **[ADR-009](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-009-redis-caching.md)** | Redis cache and rate limiting | 🟩 Approved | Infrastructure |
| **[ADR-010](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-010-nextjs-frontend.md)** | Next.js frontend web interface | 🟩 Approved | UI Application |
| **[ADR-011](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-011-langgraph-agent-orchestration.md)** | LangGraph agent orchestration | 🟩 Approved | Agent Runtime |
| **[ADR-012](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-012-postgresql-system-of-record.md)** | PostgreSQL system of record | 🟩 Approved | Data Platform |
| **[ADR-013](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-013-minio-object-storage.md)** | MinIO object storage | 🟩 Approved | Artifacts |
