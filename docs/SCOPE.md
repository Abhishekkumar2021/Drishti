# Drishti — Product scope

## Implemented ingestion

| Type | Extensions / paths | Parser |
|------|-------------------|--------|
| Code (AST) | `.py`, `.java`, `.js`/`.ts`, `.go` | Tree-sitter |
| Markdown | `.md`, `.mdx` | Header hierarchy |
| PDF | `.pdf` | PyMuPDF layout + tables |
| OpenAPI | `openapi.yaml`, `swagger.json`, etc. | Per-endpoint chunks |

Flow: `POST /api/v1/ingest` with `repo_path` or `repo_url` → incremental indexer → Qdrant.

## Planned (EPIC-04 remainder)

- **US-04.04** — Diagram / image vision descriptions (Claude Vision)

## Re-index shows “0 chunks”?

Incremental ingest only reports **new** chunks. If HEAD is unchanged, `chunks_indexed` is 0 while the store may already hold data. Check `total_chunks_in_store` in the API response or use **Force full re-index**.

## Adding languages

Each new programming language needs Tree-sitter queries and tests — see EPIC-03 pattern in `src/drishti/ingestion/ast/`.
