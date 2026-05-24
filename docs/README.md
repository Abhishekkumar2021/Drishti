# Drishti (दृष्टि) Documentation Hub

Welcome to the documentation hub for **Drishti**, a multi-modal, AST-aware Retrieval-Augmented Generation (RAG) system for code and document understanding.

This repository is **documentation-first**: architecture, ADRs, product epics, LLD chapters, and diagrams are maintained alongside code so the system can be understood without reading every module.

---

## Start Here

| I want to… | Go to |
|------------|-------|
| Understand the mission | [Product Vision](product/PRODUCT-VISION.md) |
| See system diagrams (C4, sequences, deployment) | [Architecture README](architecture/README.md) |
| Know what's built vs planned | [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) |
| Set up locally | [Onboarding](onboarding/README.md) · [Operations](operations/README.md) |
| Review API shapes | [API Contracts](design/api-contracts.md) |
| Configure embedding/LLM providers | [Model Providers](design/model-providers.md) |
| Understand chunk data | [Universal Chunk Schema](design/universal-chunk-schema.md) |

---

## Documentation Map

### Product & Planning

| Directory | Description | Status |
|-----------|-------------|--------|
| [product/](product/README.md) | Vision, 12 epics, release plan, user stories | 📖 Complete |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | Live build tracker (epics / stories) | 📖 Maintained |

### Architecture & System Design

| Document | Description |
|----------|-------------|
| [architecture/README.md](architecture/README.md) | **Hub** — diagram index, reading order |
| [architecture/high-level-architecture.md](architecture/high-level-architecture.md) | Target HLA: ingestion, storage, search, NFRs |
| [architecture/c4-model.md](architecture/c4-model.md) | C4 Context / Container / Component (Mermaid) |
| [architecture/as-built-code-ingestion.md](architecture/as-built-code-ingestion.md) | Implemented Tree-sitter pipeline (EPIC-03) |
| [architecture/sequence-diagrams.md](architecture/sequence-diagrams.md) | Health, parse, ingest, search sequences |
| [architecture/deployment-topology.md](architecture/deployment-topology.md) | Docker, CI, local vs production |

### Design & Contracts

| Document | Description |
|----------|-------------|
| [design/README.md](design/README.md) | Design specs index |
| [design/api-contracts.md](design/api-contracts.md) | REST & WebSocket contracts |
| [design/model-providers.md](design/model-providers.md) | Embedding, LLM, rerank provider configuration |
| [design/universal-chunk-schema.md](design/universal-chunk-schema.md) | Chunk field reference + ER diagram |

### Low-Level Design (LLD)

| Chapter | Topic |
|---------|-------|
| [lld/README.md](lld/README.md) | Index + interview priorities |
| [01 — Design patterns](lld/01-design-patterns.md) | Registry, strategy, factories |
| [02 — Data models](lld/02-data-models.md) | Pydantic, Qdrant, Neo4j |
| [03 — Chunking strategies](lld/03-chunking-strategies.md) | Tree-sitter, rules, metadata |
| [04 — Search pipeline](lld/04-search-pipeline.md) | Hybrid search, RRF, rerank |
| [05 — Evaluation](lld/05-evaluation-framework.md) | RAGAS, golden sets |

### Decisions & Proposals

| Directory | Description |
|-----------|-------------|
| [adr/](adr/README.md) | Architecture Decision Records (001–010) |
| [rfc/](rfc/README.md) | RFC process for proposed features |

### Deep-Dives & Evaluation

| Directory | Description |
|-----------|-------------|
| [deep-dives/](deep-dives/README.md) | Tree-sitter, embeddings, hybrid search, PDF, RAG eval |
| [evaluation/](evaluation/README.md) | Metrics, baselines, methodology |
| [model-card.md](model-card.md) | AI model card (compliance) |

### Operations & Onboarding

| Document | Description |
|----------|-------------|
| [onboarding/README.md](onboarding/README.md) | 30-minute contributor path |
| [operations/README.md](operations/README.md) | Runbook, CI, troubleshooting |

---

## Diagram Conventions

- Diagrams use **Mermaid** embedded in Markdown (GitHub-native).
- **Solid** flows = implemented; **dotted / labeled "planned"** = target state.
- As-built vs target is always cross-linked to [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

---

## Connected Narrative: Pravah & Drishti

Drishti is designed as a sister project to [Pravah (प्रवाह)](https://github.com/Abhishekkumar2021/Pravah).

- **Pravah** orchestrates the *flow* and synchronization of streaming data.
- **Drishti** provides the *vision* and comprehension to query and understand large codebases and documents.

---

## Recommended Reading Order

1. [Product Vision](product/PRODUCT-VISION.md) — the *why*
2. [C4 Model](architecture/c4-model.md) — the *shape*
3. [High-Level Architecture](architecture/high-level-architecture.md) — the *pipelines*
4. [As-built ingestion](architecture/as-built-code-ingestion.md) — the *current code path*
5. [ADRs](adr/README.md) — the *technology choices*
6. [LLD Chapter 03](lld/03-chunking-strategies.md) — the *core innovation*
7. [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md) — the *progress*
