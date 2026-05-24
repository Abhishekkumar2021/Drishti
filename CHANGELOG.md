# Changelog

All notable changes to Drishti will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation structure (ADRs, epics, LLD, deep-dives)
- Product vision and release plan
- Architecture documentation suite: C4 model, as-built ingestion, sequence diagrams, deployment topology
- Design reference for Universal Chunk schema (field table, ER diagram)
- Onboarding guide and operations runbook
- EPIC-03 metadata enrichment on `UniversalChunk` (US-03.07–03.09)
- Git incremental indexer with `IncrementalIndexer` and `ChunkIndex` (US-03.10)
- EPIC-05 embedding and vector storage (US-05.01–05.04)
  - OpenAI dense embeddings with batching/retries; `HashingDenseEmbedder` for tests
  - BM25 sparse encoder and `ChunkEmbeddingPipeline`
  - `QdrantChunkStore` with hybrid dense+sparse vectors, payload indexes, and filter compilation
- Provider-agnostic model configuration (`EMBEDDING_PROVIDER`, `LLM_PROVIDER`, `RERANK_PROVIDER`)
  - Embedding: OpenAI, Cohere, Ollama, OpenAI-compatible endpoints, hashing (tests)
  - LLM: Anthropic, OpenAI, Ollama, OpenAI-compatible, mock (with SSE streaming)
  - `create_dense_embedder()` and `create_chat_llm()` factories; runtime config validation
- EPIC-07 RAG pipeline and generation (US-07.01–07.04)
  - `ContextBuilder`, `RAGPipeline`, citation parser, SSE streaming helpers
  - `build_rag_pipeline` factory
- EPIC-06 hybrid search engine (US-06.01–06.05)
  - Dense and sparse Qdrant retrievers, RRF fusion, Cohere reranker, Anthropic query expansion
  - `HybridSearchPipeline` and `build_hybrid_search_pipeline` factory; `LexicalReranker` for local/tests
- EPIC-08 API and backend service (US-08.01–08.04)
  - `/api/v1/ingest`, `/api/v1/search`, `/api/v1/ask` (SSE) routes wired to pipelines
  - Redis `QueryCache` with TTL and invalidation on ingest
  - `RateLimitMiddleware` with per-IP Redis counters (429 on breach)

---

## [0.1.0] - 2025-05-24

### Added
- Project scaffold with Python 3.12 + FastAPI
- `pyproject.toml` with full dependency list and dev tooling (ruff, mypy, pytest)
- `Dockerfile` with multi-stage build and health check
- `docker-compose.yml` for local development (Qdrant, Redis)
- `Makefile` with setup, dev, test, lint, and pre-commit targets
- GitHub Actions CI pipeline (lint, test with Qdrant/Redis, Docker build)
- Issue templates (bug report, feature request) and PR template
- `README.md` with architecture diagram, tech stack, and quick start
- `AGENTS.md` — AI coding assistant guidelines
- `CONTRIBUTING.md` — branch strategy and PR workflow
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1
- `SECURITY.md` — vulnerability reporting process
- FastAPI application skeleton with health check endpoint
- Pydantic configuration management (`config.py`)
- Source package structure (`src/drishti/` with all submodules)
- Test directory structure (unit, integration, e2e)

[Unreleased]: https://github.com/Abhishekkumar2021/Drishti/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Abhishekkumar2021/Drishti/releases/tag/v0.1.0
