# Architecture Documentation

Architecture documents describe **what Drishti is**, **how components interact**, and **what is implemented today** versus planned.

---

## Reading Order

| Order | Document | Audience | Focus |
|-------|----------|----------|-------|
| 1 | [High-Level Architecture](high-level-architecture.md) | Everyone | End-to-end target system, NFRs, storage, search |
| 2 | [C4 Model](c4-model.md) | Architects, leads | Context → Container → Component views |
| 3 | [As-Built: Code Ingestion](as-built-code-ingestion.md) | Backend engineers | Tree-sitter pipeline **implemented in EPIC-03** |
| 4 | [Sequence Diagrams](sequence-diagrams.md) | Backend, SRE | Request/ingest lifecycles |
| 5 | [Deployment Topology](deployment-topology.md) | DevOps, SRE | Docker, CI, local vs production layout |

---

## Diagram Index

All Mermaid diagrams are version-controlled in Markdown (render on GitHub, VS Code, Cursor).

| Diagram | Location |
|---------|----------|
| System context (C4 L1) | [c4-model.md § Context](c4-model.md#level-1-system-context) |
| Containers (C4 L2) | [c4-model.md § Containers](c4-model.md#level-2-container-diagram) |
| Ingestion components (C4 L3) | [c4-model.md § Ingestion](c4-model.md#level-3-component-ingestion) |
| Target pipeline (HLA) | [high-level-architecture.md § Overview](high-level-architecture.md#2-system-architecture-overview) |
| Parser registry flow | [as-built-code-ingestion.md](as-built-code-ingestion.md) |
| Ingest / health sequences | [sequence-diagrams.md](sequence-diagrams.md) |
| Docker & CI topology | [deployment-topology.md](deployment-topology.md) |

---

## Implementation vs Target

| Layer | Target doc | As-built status |
|-------|------------|-----------------|
| FastAPI gateway, health, config | HLA §7 | 🟩 Implemented (EPIC-01) |
| File walker + language detection | [as-built-code-ingestion.md](as-built-code-ingestion.md) | 🟩 Implemented (US-03.01) |
| Tree-sitter parsers (Py, Java, JS/TS, Go) | [as-built-code-ingestion.md](as-built-code-ingestion.md) | 🟩 Implemented (US-03.02–05) |
| Parser rules + `min_chunk_lines` | [as-built-code-ingestion.md](as-built-code-ingestion.md) | 🟩 Implemented (US-03.06) |
| Metadata enrichment (docstring, complexity) | [universal-chunk-schema.md](../design/universal-chunk-schema.md) | 🟩 Implemented (US-03.07–09) |
| Git incremental walker | [as-built-code-ingestion.md](as-built-code-ingestion.md) §7 | 🟩 Implemented (US-03.10) |
| Embeddings + Qdrant write path | HLA §4 | 🔮 Planned (EPIC-05) |
| Hybrid search + RAG generation | HLA §5–6 | 🔮 Planned (EPIC-06–07) |

Live checklist: [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md).

---

## Related Documentation

- [Design: Universal Chunk Schema](../design/universal-chunk-schema.md)
- [LLD: Chunking Strategies](../lld/03-chunking-strategies.md)
- [ADR Index](../adr/README.md)
- [Operations Runbook](../operations/README.md)
