# Sequence Diagrams

End-to-end lifecycles for Drishti services. **Solid** flows are implemented; **dotted** flows are planned.

---

## Health & Readiness (Implemented)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant API as FastAPI
    participant H as health.py
    participant Q as Qdrant
    participant R as Redis

    C->>API: GET /health/live
    API-->>C: 200 OK (process up)

    C->>API: GET /health/ready
    API->>H: probe_dependencies()
    H->>Q: TCP / collection check
    H->>R: PING
    Q-->>H: ok / degraded
    R-->>H: ok / degraded
    H-->>API: ServiceStatus map
    API-->>C: 200 or 503 + JSON body
```

---

## Code File Parse (Implemented)

```mermaid
sequenceDiagram
    autonumber
    participant W as FileWalker
    participant R as ParserRegistry
    participant P as TreeSitterParser
    participant S as UniversalChunk

    W->>W: detect language + extension
    W->>R: get_parser(relative_path)
    R-->>P: parser instance
    W->>P: parse(bytes, path)
    P->>P: Tree-sitter + QueryCursor
    P-->>S: list[UniversalChunk]
```

---

## Full Repository Ingest (Target)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant API as FastAPI
    participant W as FileWalker
    participant P as Parsers
    participant E as EmbeddingService
    participant Q as Qdrant

    C->>API: POST /ingest { repo_path }
    API->>W: discover files
    loop each code file
        W->>P: parse → chunks
        P-->>API: UniversalChunk[]
        API->>E: embed dense + sparse
        E->>Q: upsert points
    end
    API-->>C: job summary + counts
```

> Embedding and Qdrant upsert are implemented (`ChunkEmbeddingPipeline`, `QdrantChunkStore`) but **not yet wired to the HTTP API** (EPIC-08).

---

## Hybrid Search & Ask (Target)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant API as FastAPI
    participant X as Query expander
    participant Q as Qdrant
    participant F as RRF fusion
    participant RR as Cohere rerank
    participant CTX as Context builder
    participant LLM as Claude

    C->>API: POST /ask { question }
    API->>X: expand query
    par Dense + sparse
        API->>Q: vector search
        API->>Q: BM25 search
    end
    Q-->>F: candidate lists
    F->>RR: fused ranking
    RR->>CTX: top-k chunks + metadata
    CTX->>LLM: prompt + citations
    LLM-->>API: streamed tokens
    API-->>C: SSE answer + sources
```

---

## Incremental Indexing (Implemented — US-03.10)

```mermaid
sequenceDiagram
    autonumber
    participant API as Ingestion job
    participant G as Git diff
    participant ST as Index state store
    participant Q as Qdrant

    API->>G: diff(indexed_commit, HEAD)
    G-->>API: added, modified, deleted paths
    API->>ST: read last_indexed_sha
  loop deleted
        API->>Q: delete by file_path filter
    end
  loop added + modified
        API->>API: parse + embed + upsert
    end
    API->>ST: write HEAD sha
```

---

## Cross-References

- [As-built ingestion](as-built-code-ingestion.md)
- [API contracts](../design/api-contracts.md)
- [Search pipeline LLD](../lld/04-search-pipeline.md)
