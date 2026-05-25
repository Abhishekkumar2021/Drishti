# Implementation Status: Drishti (दृष्टि)

This file is the living source of truth for the current build status of Drishti. It tracks progress at the Epic and User Story levels.

*Last Updated: 2026-05-24*

---

## Table of Contents

1. [Overall Summary](#1-overall-summary)
2. [Phase Progression](#2-phase-progression)
3. [Detailed Epic Status](#3-detailed-epic-status)
4. [File Mapping & Code Integrations](#4-file-mapping--code-integrations)

---

## 1. Overall Summary

| Component | Total Points | Completed | Progress % | Status |
|-----------|--------------|-----------|------------|--------|
| **Phase 1: Foundation** | 55 | 55 | 100.0% | 🟩 Completed |
| **Phase 2: Ingestion** | 131 | 89 | 67.9% | 🟨 In Progress |
| **Phase 3: Core Search & RAG** | 131 | 131 | 100.0% | 🟩 Completed |
| **Phase 4: Advanced Features** | 89 | 47 | 52.8% | 🟨 In Progress |
| **Phase 5: Evaluation** | 34 | 0 | 0.0% | 🔮 Planned |
| **Phase 6: Release** | 21 | 0 | 0.0% | 🔮 Planned |
| **Total Project** | **461** | **322** | **69.8%** | **🟨 In Progress** |

---

## 2. Phase Progression

```
Phase 1: Foundation     [████████████████████] 100.0% (Completed)
Phase 2: Ingestion      [█████████████░░░░░░░] 67.9% (In Progress)
Phase 3: Search & RAG   [████████████████████] 100.0% (Completed)
Phase 4: UI & Graph     [██████████░░░░░░░░░░] 52.8% (In Progress)
Phase 5: Evaluation     [░░░░░░░░░░░░░░░░░░░] 0.0%  (Planned)
Phase 6: Release        [░░░░░░░░░░░░░░░░░░░] 0.0%  (Planned)
```

---

## 3. Detailed Epic Status

### Phase 1: Foundation (Epics 01–02)

#### EPIC-01: Project Setup & Documentation (Priority: P0)
* **Points**: 21 | **Status**: 🟩 Completed (100%)
* **Stories**:
  * [x] **US-01.01**: Python structure + UV package manager (`pyproject.toml`)
  * [x] **US-01.02**: Docker setup (Qdrant, Redis)
  * [x] **US-01.03**: GitHub Actions CI workflow setup
  * [x] **US-01.04**: Initial root documents (README.md, Makefile)
  * [x] **US-01.05**: Community documents (CONTRIBUTING.md, AGENTS.md, CODE_OF_CONDUCT.md, SECURITY.md)

#### EPIC-02: Documentation & Process (Priority: P0)
* **Points**: 34 | **Status**: 🟩 Completed (100%)
* **Stories**:
  * [x] **US-02.01**: PRODUCT-VISION.md
  * [x] **US-02.02**: EPICS-OVERVIEW.md
  * [x] **US-02.03**: 12 Epic detailed documents (in `docs/product/epics/`)
  * [x] **US-02.04**: 10 Tech ADRs (in `docs/adr/`)
  * [x] **US-02.05**: High-Level Architecture (HLA) document
  * [x] **US-02.06**: Initalize IMPLEMENTATION_STATUS.md
  * [x] **US-02.07**: RELEASE-PLAN.md

---

### Phase 2: Ingestion & Storage (Epics 03–05)

#### EPIC-03: Code Ingestion Pipeline (Priority: P0)
* **Points**: 55 | **Status**: 🟩 Completed (100%)
* **Stories**:
  * [x] **US-03.01**: File walk and programming language detection
  * [x] **US-03.02**: Python Tree-sitter integration
  * [x] **US-03.03**: Java Tree-sitter integration
  * [x] **US-03.04**: JavaScript/TypeScript Tree-sitter integration
  * [x] **US-03.05**: Go Tree-sitter integration
  * [x] **US-03.06**: AST node extraction rule engine
  * [x] **US-03.07**: Metadata enrichment (parameters, complexity, docstrings)
  * [x] **US-03.08**: Parent/child relationship linking (method → class)
  * [x] **US-03.09**: Dependency/import extraction
  * [x] **US-03.10**: Repository git walker (incremental indexing via diffs)

#### EPIC-04: Document Ingestion Pipeline (Priority: P1)
* **Points**: 42 | **Status**: 🟨 In Progress (~81% — vision deferred)
* **Stories**:
  * [x] **US-04.01**: PDF layout-aware parser (PyMuPDF) — `src/drishti/ingestion/documents/pdf.py`
  * [x] **US-04.02**: PDF table structure extraction (markdown tables in PDF parser)
  * [x] **US-04.03**: Markdown header hierarchy parser — `src/drishti/ingestion/documents/markdown.py`
  * [ ] **US-04.04**: Multi-modal image analysis (Claude Vision API)
  * [x] **US-04.05**: OpenAPI spec endpoint parser — `src/drishti/ingestion/documents/openapi.py`

#### EPIC-05: Embedding & Vector Storage (Priority: P0)
* **Points**: 34 | **Status**: 🟩 Completed (100%)
* **Stories**:
  * [x] **US-05.01**: Dense embedding integration (OpenAI default; `EMBEDDING_PROVIDER` for any model)
  * [x] **US-05.02**: Sparse embedding (BM25 tokenizer)
  * [x] **US-05.03**: Qdrant database client initialization and index schemas
  * [x] **US-05.04**: Payload-based metadata filter compilation

---

### Phase 3: Core Search & RAG (Epics 06–08)

#### EPIC-06: Hybrid Search Engine (Priority: P0)
* **Points**: 55 | **Status**: 🟩 Completed (100%)
* **Stories**:
  * [x] **US-06.01**: Dense vector retriever
  * [x] **US-06.02**: Sparse BM25 retriever
  * [x] **US-06.03**: Reciprocal Rank Fusion (RRF) combiner
  * [x] **US-06.04**: Cohere re-ranking integration
  * [x] **US-06.05**: LLM query expansion implementation

#### EPIC-07: RAG Pipeline & Generation (Priority: P0)
* **Points**: 42 | **Status**: 🟩 Completed (100%)
* **Stories**:
  * [x] **US-07.01**: Prompt template compiler & context builder
  * [x] **US-07.02**: LLM client integration (`create_chat_llm`, provider-agnostic)
  * [x] **US-07.03**: Streaming response mechanism (SSE events)
  * [x] **US-07.04**: Citation parser & line reference generator

#### EPIC-08: API & Backend Service (Priority: P0)
* **Points**: 34 | **Status**: 🟩 Completed (100%)
* **Stories**:
  * [x] **US-08.01**: FastAPI routing (`/ingest`, `/search`, `/ask`)
  * [x] **US-08.02**: Request validation via Pydantic
  * [x] **US-08.03**: Redis cache configuration for queries
  * [x] **US-08.04**: Rate limiting middleware

---

### Phase 4: UI & Graph DB (Epics 09–10)

#### EPIC-09: Dependency Graph & Impact Analysis (Priority: P2)
* **Points**: 34 | **Status**: 🔮 Planned (0%)
* **Stories**:
  * [ ] **US-09.01**: Neo4j database setup & schema definition
  * [ ] **US-09.02**: Graph builder (node creation for methods, files, packages)
  * [ ] **US-09.03**: Dependency tracing algorithm
  * [ ] **US-09.04**: Change impact analysis endpoint (`/api/v1/impact-analysis`)

#### EPIC-10: Frontend UI (Priority: P1)
* **Points**: 55 | **Status**: 🟩 Completed (US-10.05 deferred to EPIC-09)
* **Stories**:
  * [x] **US-10.01**: Next.js 14 layout & landing page
  * [x] **US-10.02**: Chat interface with streaming responses
  * [x] **US-10.03**: Monaco Editor component for source code rendering
  * [x] **US-10.04**: Citation mapping (clicking citation opens file to specific line)
  * [ ] **US-10.05**: Interactive dependency graph view (requires EPIC-09)

---

### Phase 5: Evaluation & Benchmarking (Epic 11)

#### EPIC-11: Evaluation & Benchmarking (Priority: P1)
* **Points**: 34 | **Status**: 🔮 Planned (0%)
* **Stories**:
  * [ ] **US-11.01**: Golden Q&A dataset curation
  * [ ] **US-11.02**: RAGAS evaluation runner script
  * [ ] **US-11.03**: Comparative dashboard (AST vs Naive chunking)

---

### Phase 4b: Production Platform V2 (Epics 13–17)

> Master plan: [platform-v2-agentic.md](architecture/platform-v2-agentic.md)

#### EPIC-13: Intelligent routing & workspaces (Priority: P0)
* **Points**: 34 | **Status**: 🟨 In Progress (~70%)
* **Stories**:
  * [x] Content router (magic bytes + path heuristics) — `content_router.py`
  * [x] Workspace / upload / conversation APIs — `platform_routes.py`
  * [x] Git snapshot ingest roots — `workspace_git.py`

#### EPIC-14: LangGraph agent runtime (Priority: P0)
* **Points**: 34 | **Status**: 🟨 In Progress (~40%)
* **Stories**:
  * [x] Retrieve → generate → grade graph — `agent/graph.py`, `agent/runner.py`, `agent/nodes.py`
  * [x] Single LangGraph agent path for all `/ask` endpoints
  * [x] Postgres checkpointer for multi-turn agent state — `agent/checkpointer.py`

#### EPIC-15: Data platform (Priority: P0)
* **Points**: 34 | **Status**: 🟨 In Progress (~55%)
* **Stories**:
  * [x] PostgreSQL models + Alembic — `db/models.py`, `alembic/versions/001_*`
  * [x] `PlatformService` (Postgres + filesystem fallback)
  * [x] MinIO artifact storage — `storage/artifacts.py` (`ENABLE_MINIO=true`)
  * [x] Arq ingest worker — `worker/tasks.py`
  * [x] Conversations use Postgres when `DATABASE_URL` set (Redis store disabled)

#### EPIC-16: Auth, RBAC, observability (Priority: P1)
* **Points**: 21 | **Status**: 🟨 In Progress (~35%)
* **Stories**:
  * [x] Structured JSON logging (structlog) — `observability/logging.py`
  * [x] Request ID + log correlation — `middleware/request_id.py`, `logging_context.py`
  * [x] Health probes for Postgres + MinIO
  * [ ] OIDC / enterprise SSO
  * [ ] OpenTelemetry traces

#### EPIC-17: UI parity (Priority: P1)
* **Points**: 21 | **Status**: 🔮 Planned (0%)

---

### Phase 6: Release (Epic 12)

#### EPIC-12: Demo, Polish & Deployment (Priority: P1)
* **Points**: 21 | **Status**: 🔮 Planned (0%)
* **Stories**:
  * [ ] **US-12.01**: Seed script for sample projects
  * [ ] **US-12.02**: Docker production optimization
  * [ ] **US-12.03**: Final release package deployment guidelines

---

## 4. File Mapping & Code Integrations

Once a User Story is implemented, the corresponding code files must be registered below:

| Story ID | Target File | Status | Tests |
|----------|-------------|--------|-------|
| US-01.01 | [pyproject.toml](file:///Users/abhishek/Dev/Drishti/pyproject.toml) | 🟩 Completed | - |
| US-01.02 | [docker-compose.yml](file:///Users/abhishek/Dev/Drishti/docker-compose.yml), [Dockerfile](file:///Users/abhishek/Dev/Drishti/Dockerfile) | 🟩 Completed | - |
| US-01.03 | [.github/workflows/ci.yml](file:///Users/abhishek/Dev/Drishti/.github/workflows/ci.yml) | 🟩 Completed | - |
| US-01.04 | [README.md](file:///Users/abhishek/Dev/Drishti/README.md), [Makefile](file:///Users/abhishek/Dev/Drishti/Makefile) | 🟩 Completed | - |
| US-01.05 | [AGENTS.md](file:///Users/abhishek/Dev/Drishti/AGENTS.md), [CONTRIBUTING.md](file:///Users/abhishek/Dev/Drishti/CONTRIBUTING.md), [CODE_OF_CONDUCT.md](file:///Users/abhishek/Dev/Drishti/CODE_OF_CONDUCT.md), [SECURITY.md](file:///Users/abhishek/Dev/Drishti/SECURITY.md) | 🟩 Completed | - |
| US-02.01 | [PRODUCT-VISION.md](file:///Users/abhishek/Dev/Drishti/docs/product/PRODUCT-VISION.md) | 🟩 Completed | - |
| US-02.02 | [EPICS-OVERVIEW.md](file:///Users/abhishek/Dev/Drishti/docs/product/EPICS-OVERVIEW.md) | 🟩 Completed | - |
| US-02.03 | [docs/product/epics/](file:///Users/abhishek/Dev/Drishti/docs/product/epics/) | 🟩 Completed | - |
| US-02.04 | [docs/adr/](file:///Users/abhishek/Dev/Drishti/docs/adr/) | 🟩 Completed | - |
| US-02.05 | [high-level-architecture.md](file:///Users/abhishek/Dev/Drishti/docs/architecture/high-level-architecture.md) | 🟩 Completed | - |
| US-02.06 | [IMPLEMENTATION_STATUS.md](file:///Users/abhishek/Dev/Drishti/docs/IMPLEMENTATION_STATUS.md) | 🟩 Completed | - |
| US-02.07 | [RELEASE-PLAN.md](file:///Users/abhishek/Dev/Drishti/docs/product/releases/RELEASE-PLAN.md) | 🟩 Completed | - |
| US-03.01 | [walker.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/walker.py), [language.py](file:///Users/abhishek/Dev/Drishti/src/drishti/utils/language.py), [gitignore.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/gitignore.py), [base.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/base.py), [schemas.py](file:///Users/abhishek/Dev/Drishti/src/drishti/api/schemas.py) | 🟩 Completed | [test_walker.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_walker.py), [test_language.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_language.py), [test_gitignore.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_gitignore.py) |
| US-03.02 | [ast/base.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/base.py), [ast/python.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/python.py), [ast/registry.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/registry.py), [queries/python.scm](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/queries/python.scm) | 🟩 Completed | [test_python_parser.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_python_parser.py) |
| US-03.03 | [ast/java.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/java.py), [queries/java.scm](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/queries/java.scm) | 🟩 Completed | [test_java_parser.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_java_parser.py) |
| US-03.04 | [ast/ecmascript.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/ecmascript.py), [ast/javascript.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/javascript.py), [ast/typescript.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/typescript.py), [queries/javascript.scm](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/queries/javascript.scm), [queries/typescript.scm](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/queries/typescript.scm) | 🟩 Completed | [test_javascript_parser.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_javascript_parser.py), [test_typescript_parser.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_typescript_parser.py) |
| US-03.05 | [ast/go.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/go.py), [queries/go.scm](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/queries/go.scm) | 🟩 Completed | [test_go_parser.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_go_parser.py) |
| US-03.06 | [ast/rules.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/rules.py), [ast/catalog.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/catalog.py), [queries/parser_rules.json](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/queries/parser_rules.json) | 🟩 Completed | [test_parser_rules.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_parser_rules.py) |
| US-03.07 | [ast/metadata.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/metadata.py), [schemas.py](file:///Users/abhishek/Dev/Drishti/src/drishti/api/schemas.py) | 🟩 Completed | [test_metadata_enrichment.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_metadata_enrichment.py) |
| US-03.08 | [ast/metadata.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/metadata.py) | 🟩 Completed | [test_metadata_enrichment.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_metadata_enrichment.py) |
| US-03.09 | [symbols.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/symbols.py), [ast/metadata.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/ast/metadata.py) | 🟩 Completed | [test_metadata_enrichment.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_metadata_enrichment.py) |
| US-03.10 | [git_changes.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/git_changes.py), [incremental.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/incremental.py), [index_state.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/index_state.py), [chunk_index.py](file:///Users/abhishek/Dev/Drishti/src/drishti/ingestion/chunk_index.py) | 🟩 Completed | [test_git_incremental.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_git_incremental.py) |
| US-05.01 | [embedding/factory.py](file:///Users/abhishek/Dev/Drishti/src/drishti/embedding/factory.py), [dense.py](file:///Users/abhishek/Dev/Drishti/src/drishti/embedding/dense.py), [openai_compatible.py](file:///Users/abhishek/Dev/Drishti/src/drishti/embedding/openai_compatible.py), [cohere_dense.py](file:///Users/abhishek/Dev/Drishti/src/drishti/embedding/cohere_dense.py), [ollama_dense.py](file:///Users/abhishek/Dev/Drishti/src/drishti/embedding/ollama_dense.py), [model-providers.md](file:///Users/abhishek/Dev/Drishti/docs/design/model-providers.md) | 🟩 Completed | [test_dense_embedding.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_dense_embedding.py), [test_provider_factories.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_provider_factories.py) |
| US-05.02 | [sparse.py](file:///Users/abhishek/Dev/Drishti/src/drishti/embedding/sparse.py) | 🟩 Completed | [test_sparse_embedding.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_sparse_embedding.py) |
| US-05.03 | [schema.py](file:///Users/abhishek/Dev/Drishti/src/drishti/storage/schema.py), [qdrant_store.py](file:///Users/abhishek/Dev/Drishti/src/drishti/storage/qdrant_store.py), [pipeline.py](file:///Users/abhishek/Dev/Drishti/src/drishti/embedding/pipeline.py) | 🟩 Completed | [test_qdrant_chunk_store.py](file:///Users/abhishek/Dev/Drishti/tests/integration/test_qdrant_chunk_store.py), [test_embedding_pipeline.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_embedding_pipeline.py) |
| US-05.04 | [filters.py](file:///Users/abhishek/Dev/Drishti/src/drishti/storage/filters.py) | 🟩 Completed | [test_storage_filters.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_storage_filters.py) |
| US-06.01 | [dense.py](file:///Users/abhishek/Dev/Drishti/src/drishti/search/dense.py) | 🟩 Completed | [test_dense_retriever.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_dense_retriever.py) |
| US-06.02 | [sparse.py](file:///Users/abhishek/Dev/Drishti/src/drishti/search/sparse.py) | 🟩 Completed | [test_sparse_retriever.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_sparse_retriever.py) |
| US-06.03 | [rrf.py](file:///Users/abhishek/Dev/Drishti/src/drishti/search/rrf.py) | 🟩 Completed | [test_rrf.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_rrf.py) |
| US-06.04 | [rerank.py](file:///Users/abhishek/Dev/Drishti/src/drishti/search/rerank.py) | 🟩 Completed | [test_search_rerank.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_search_rerank.py) |
| US-06.05 | [expansion.py](file:///Users/abhishek/Dev/Drishti/src/drishti/search/expansion.py), [generation/factory.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/factory.py), [generation/llm.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/llm.py) | 🟩 Completed | [test_query_expansion.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_query_expansion.py), [test_provider_factories.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_provider_factories.py) |
| US-06.* | [pipeline.py](file:///Users/abhishek/Dev/Drishti/src/drishti/search/pipeline.py), [factory.py](file:///Users/abhishek/Dev/Drishti/src/drishti/search/factory.py) | 🟩 Completed | [test_hybrid_search_pipeline.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_hybrid_search_pipeline.py), [test_hybrid_search.py](file:///Users/abhishek/Dev/Drishti/tests/integration/test_hybrid_search.py) |
| US-07.01 | [generation/context.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/context.py), [generation/prompts.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/prompts.py) | 🟩 Completed | [test_context_builder.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_context_builder.py) |
| US-07.02 | [generation/llm.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/llm.py), [generation/factory.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/factory.py) | 🟩 Completed | [test_generation_llm.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_generation_llm.py) |
| US-07.03 | [generation/streaming.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/streaming.py), [generation/pipeline.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/pipeline.py) | 🟩 Completed | [test_rag_pipeline.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_rag_pipeline.py) |
| US-07.04 | [generation/citations.py](file:///Users/abhishek/Dev/Drishti/src/drishti/generation/citations.py) | 🟩 Completed | [test_citations.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_citations.py) |
| US-08.01 | [api/routes.py](file:///Users/abhishek/Dev/Drishti/src/drishti/api/routes.py), [main.py](file:///Users/abhishek/Dev/Drishti/src/drishti/main.py) | 🟩 Completed | [test_api_routes.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_api_routes.py), [test_main.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_main.py) |
| US-08.02 | [api/schemas.py](file:///Users/abhishek/Dev/Drishti/src/drishti/api/schemas.py), [api/responses.py](file:///Users/abhishek/Dev/Drishti/src/drishti/api/responses.py) | 🟩 Completed | [test_schemas.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_schemas.py) |
| US-08.03 | [services/query_cache.py](file:///Users/abhishek/Dev/Drishti/src/drishti/services/query_cache.py) | 🟩 Completed | [test_query_cache.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_query_cache.py) |
| US-08.04 | [middleware/rate_limit.py](file:///Users/abhishek/Dev/Drishti/src/drishti/middleware/rate_limit.py) | 🟩 Completed | [test_rate_limit.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_rate_limit.py) |
| US-10.01–04 | [web/](file:///Users/abhishek/Dev/Drishti/web/), [api/routes.py](file:///Users/abhishek/Dev/Drishti/src/drishti/api/routes.py) (`/source/read`) | 🟩 Completed | [test_source_read.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_source_read.py), `npm run build` in `web/` |
| EPIC-14 | [agent/](file:///Users/abhishek/Dev/Drishti/src/drishti/agent/), [ADR-011](file:///Users/abhishek/Dev/Drishti/docs/adr/ADR-011-langgraph-agent-orchestration.md) | 🟨 In Progress | [test_agent_graph.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_agent_graph.py) |
| EPIC-15 | [db/](file:///Users/abhishek/Dev/Drishti/src/drishti/db/), [platform_service.py](file:///Users/abhishek/Dev/Drishti/src/drishti/services/platform_service.py), [alembic/](file:///Users/abhishek/Dev/Drishti/alembic/) | 🟨 In Progress | [test_platform_service.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_platform_service.py) |
| EPIC-16 | [observability/](file:///Users/abhishek/Dev/Drishti/src/drishti/observability/) | 🟨 In Progress | [test_structured_logging.py](file:///Users/abhishek/Dev/Drishti/tests/unit/test_structured_logging.py) |
