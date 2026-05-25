# Production roadmap — from RAG demo to enterprise platform (V1)

> **Platform V2 (LangGraph, Postgres, MinIO, agent memory):** see **[platform-v2-agentic.md](platform-v2-agentic.md)** — this is the master plan for competing with production assistants on **grounded code/docs Q&A**.

## What we have today (honest)

| Capability | Status |
|------------|--------|
| AST code indexing (git repos) | Production-ready core |
| Document parsers (md/pdf/openapi) | Implemented (EPIC-04) |
| Hybrid search + streaming RAG | Production-ready core |
| Client-sent chat history on `/ask` | Works, not persisted |
| **Intelligent file routing** | **New — content + magic bytes** |
| **Server-side conversations** | **New — Redis (`/conversations`)** |
| **Workspace uploads** | **New — multipart artifacts API** |
| **Agent memory** | **New — manual workspace memory API** |
| Multi-tenant auth / SSO | Not yet |
| Auto memory summarization | Not yet (manual `PUT /memory`) |
| S3 uploads, virus scan, quotas per org | Not yet |
| EPIC-09 dependency graph | Planned |
| EPIC-11 RAG evaluation CI | Planned |

## Intelligent routing (not “dumb extensions”)

`ContentRouter` (`src/drishti/ingestion/content_router.py`) classifies each file using:

1. **Magic bytes** — `%PDF-`, Java class files, Python shebangs.
2. **Content sniffing** — `openapi:` in YAML, JSON schema keys, Markdown heading patterns.
3. **Path heuristics** — `openapi.yaml`, `README` without extension.
4. **Extension map** — fallback for known code types.

The indexer selects parsers via `effective_extension`, so a misnamed `.bin` PDF is still parsed correctly.

## Conversations vs memory

- **Conversation** = short-term turn history (Redis, 7-day TTL default), used automatically in `/conversations/{id}/ask`.
- **Workspace memory** = long-term notes you set via API (team facts, glossary, architecture decisions). Injected into every RAG prompt for that workspace.

Automatic “the agent remembers everything” (LLM compaction, entity extraction) is **US-13.05** — not silent yet by design (avoids hidden cost/hallucinated memory).

## Workspaces & artifacts

```
POST /api/v1/workspaces
POST /api/v1/workspaces/{id}/artifacts  ← upload PDFs, markdown, OpenAPI
POST /api/v1/workspaces/{id}/ingest
POST /api/v1/conversations
POST /api/v1/conversations/{id}/ask     ← scoped to workspace chunks + memory
```

Chunks are stored with `file_path` prefix `workspaces/{id}/...` for filter isolation in the same Qdrant collection.

## Next production milestones

1. **EPIC-11** — Golden Q&A + RAGAS in CI (world-tested quality bar).
2. **EPIC-09** — Dependency graph + impact analysis.
3. **US-13.05** — Auth, async jobs, auto memory, cloud storage.
4. **UI** — Workspace switcher, drag-drop uploads, conversation sidebar (extend EPIC-10).
