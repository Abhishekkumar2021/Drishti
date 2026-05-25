# EPIC-13: Production Platform (Workspaces, Memory, Intelligent Routing)

**Priority:** P1 | **Status:** In Progress

## Objective

Evolve Drishti from a git-repo indexer into a production-grade knowledge platform: intelligent file routing, artifact uploads, server-side conversations, and workspace-scoped agent memory.

## User Stories

### US-13.01: Content-aware file router
- [x] Classify files by extension, magic bytes, path heuristics, and content sniffing (PDF, OpenAPI, Markdown).
- [x] Route parser selection by `effective_extension`, not filename alone.

### US-13.02: Workspaces & artifact upload
- [x] `POST /api/v1/workspaces` — isolated knowledge spaces.
- [x] `POST /api/v1/workspaces/{id}/artifacts` — multipart upload (PDF, md, specs).
- [x] Git snapshot + incremental index under `workspaces/{id}/` namespace in Qdrant payloads.

### US-13.03: Server-side conversations
- [x] `POST /api/v1/conversations` — Redis-backed session.
- [x] `POST /api/v1/conversations/{id}/ask` — loads history server-side, persists turns.

### US-13.04: Workspace agent memory
- [x] `PUT/GET /api/v1/workspaces/{id}/memory` — durable notes injected into RAG prompts.

### US-13.05: Production hardening (planned)
- [ ] Per-tenant auth / RBAC, encrypted secrets, audit logs.
- [ ] Background ingest jobs + progress webhooks.
- [ ] Automatic memory summarization after each session (LLM compaction).
- [ ] S3/GCS artifact storage backend (not only local cache).

## Dependencies

- EPIC-04 (document parsers), EPIC-08 (API), Redis, Qdrant.
