<div align="center">

# Drishti — दृष्टि

**Multi-modal, AST-aware RAG System for Code & Document Understanding**

*Sanskrit: "vision" or "sight" — see through your entire codebase*

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?style=flat-square)](https://qdrant.tech)
[![Tree-sitter](https://img.shields.io/badge/Tree--sitter-AST-4B8BBE?style=flat-square)](https://tree-sitter.github.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/Abhishekkumar2021/Drishti/ci.yml?style=flat-square&label=CI)](https://github.com/Abhishekkumar2021/Drishti/actions)

</div>

---

## What Is Drishti?

Drishti is a **retrieval-augmented generation (RAG) system** that understands codebases and documentation at a structural level. Unlike naive RAG that splits text by character count, Drishti uses **Tree-sitter** to parse code into its Abstract Syntax Tree (AST), creating semantically meaningful chunks — complete functions, classes, interfaces — not random fragments.

It also ingests PDFs, Markdown docs, diagrams, and API specs, enabling **cross-modal queries** like:

> *"Where is authentication handled?"*
> → Returns code from `AuthService.java`, quotes from the design spec PDF, and descriptions of the auth sequence diagram — all in one answer with file paths and line numbers.

> **Important distinction:** Drishti is a **knowledge retrieval system**, not a code generator. You ask questions about existing code and docs; Drishti finds, explains, and cites the relevant pieces.

### Why AST-Aware RAG?

| Approach | How It Chunks Code | Search Results | Quality |
|----------|-------------------|----------------|---------|
| **Naive RAG** | Split every 500 characters | Random fragments: half a function here, part of a class there | ❌ Poor |
| **Line-based** | Split every 50 lines | Arbitrary boundaries, loses context | ❌ Poor |
| **Drishti (AST-aware)** | Parse via Tree-sitter → extract complete functions, classes, interfaces | Whole functions with metadata: name, parameters, return type, parent class, dependencies | ✅ Excellent |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                      INGESTION PIPELINE                             │
│                                                                      │
│  Git Repo ──┐                                                        │
│  PDF Files ─┤   ┌──────────────────┐   ┌──────────────────┐         │
│  Markdown ──┼──▶│  Parser Registry │──▶│ Universal Chunk  │         │
│  Images ────┤   │  (Tree-sitter,   │   │ Schema + Metadata│         │
│  OpenAPI ───┘   │   PyMuPDF, etc.) │   └────────┬─────────┘         │
│                 └──────────────────┘            │                    │
│                                      ┌─────────┴──────────┐         │
│                                      ▼                    ▼         │
│                               Dense Embedding       BM25 Sparse     │
│                            (text-embedding-3-small)  (tokenizer)    │
│                                      │                    │         │
│                                      └────────┬───────────┘         │
│                                               ▼                     │
│                                      ┌────────────────┐             │
│                                      │  Qdrant Vector │             │
│                                      │  Database      │             │
│                                      └────────────────┘             │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                        QUERY PIPELINE                               │
│                                                                      │
│  "Where is auth handled?"                                            │
│       │                                                              │
│       ▼                                                              │
│  Query Expansion (LLM) → "auth, login, JWT, middleware"              │
│       │                                                              │
│  ┌────┴────┐                                                         │
│  ▼         ▼                                                         │
│ BM25    Vector      ──▶  RRF Fusion  ──▶  Cohere Re-rank            │
│ Search  Search                                   │                   │
│                                                  ▼                   │
│                                          Context Builder             │
│                                          (file paths, class          │
│                                           hierarchy, deps)          │
│                                                  │                   │
│                                                  ▼                   │
│                                          Claude API (streaming)      │
│                                          → Answer with citations     │
│                                          → Code snippets             │
│                                          → File paths + line nums   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description | Status |
|---------|-------------|--------|
| **AST-Aware Chunking** | Tree-sitter parses code into functions, classes, interfaces | 🔮 Planned |
| **Multi-Language** | Python, Java, JavaScript/TypeScript, Go | 🔮 Planned |
| **PDF Ingestion** | Layout-aware parsing: text blocks, tables, images | 🔮 Planned |
| **Hybrid Search** | BM25 keyword + vector semantic search with RRF fusion | 🔮 Planned |
| **Re-ranking** | Cohere rerank-v3.5 for precision | 🔮 Planned |
| **Cross-Modal Q&A** | Query code + docs + diagrams together | 🔮 Planned |
| **Streaming Answers** | Claude API with SSE streaming + citations | 🔮 Planned |
| **Impact Analysis** | "What breaks if I change X?" via dependency graph | 🔮 Planned |
| **Incremental Indexing** | Only re-index git-changed files | 🔮 Planned |
| **Code Navigation** | Click citation → file path + line number | 🔮 Planned |
| **RAG Evaluation** | RAGAS metrics: precision, recall, faithfulness | 🔮 Planned |

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Runtime** | Python 3.12 | Best ML/AI ecosystem |
| **Web Framework** | FastAPI | Async, auto-docs, Pydantic native |
| **AST Parsing** | Tree-sitter | Multi-language, incremental, fast |
| **Embeddings** | OpenAI text-embedding-3-small | Best quality/cost for code |
| **Vector DB** | Qdrant | Native hybrid search (dense+sparse) |
| **Re-ranking** | Cohere rerank-v3.5 | Best quality, free tier |
| **LLM** | Claude API | Best code understanding |
| **PDF Parsing** | PyMuPDF | Layout-aware, tables, images |
| **Graph DB** | Neo4j (optional) | Dependency graph traversal |
| **Cache** | Redis | Query result caching |
| **Frontend** | Next.js 14 + Monaco | Code highlighting, navigation |

---

## What Drishti Is NOT

- Not an IDE or code editor — it's a knowledge retrieval system
- Not a code generation tool — it *finds* and *explains* existing code
- Not a replacement for documentation — it makes documentation *searchable*
- Not a CI/CD tool — it's for understanding, not deployment

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Docker** (for Qdrant and Redis)
- **API Keys**: OpenAI, Anthropic (Claude), Cohere

### Setup

```bash
# Clone the repository
git clone https://github.com/Abhishekkumar2021/Drishti.git
cd Drishti

# First-time setup (installs uv, creates venv, installs deps)
make setup

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Start infrastructure (Qdrant, Redis)
make docker-up

# Start the API server
make dev
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Build and Test

```bash
# Run all tests
make test

# Lint + type check
make lint
make type-check

# Full pre-commit check
make pre-commit

# Run RAG evaluation benchmarks
make benchmark
```

---

## Repository Layout

```
Drishti/
├── README.md                          # You are here
├── AGENTS.md                          # AI coding assistant guidelines
├── CONTRIBUTING.md                    # Contribution guide
├── CHANGELOG.md                       # Version history
├── docs/
│   ├── README.md                      # Documentation index
│   ├── IMPLEMENTATION_STATUS.md       # What's built vs. planned
│   ├── architecture/                  # High-level architecture
│   ├── adr/                           # Architecture Decision Records (10)
│   ├── rfc/                           # Request for Comments
│   ├── lld/                           # Low-Level Design docs (5)
│   ├── product/                       # Vision, epics (12), release plan
│   ├── design/                        # API contracts
│   ├── evaluation/                    # RAG metrics & baselines
│   ├── deep-dives/                    # Technical deep-dives (5 chapters)
│   └── model-card.md                  # AI model documentation
├── src/drishti/                       # Python package
│   ├── ingestion/                     # AST + PDF + Markdown parsers
│   ├── embedding/                     # Dense + sparse embeddings
│   ├── storage/                       # Qdrant + Neo4j stores
│   ├── search/                        # Hybrid search + RRF + rerank
│   ├── generation/                    # Context builder + LLM client
│   ├── api/                           # FastAPI routes
│   └── utils/                         # Language detection, git utils
├── tests/                             # Unit, integration, e2e tests
├── benchmarks/                        # RAG evaluation scripts
├── notebooks/                         # Jupyter tutorials
├── playground/                        # Standalone learning modules
├── web/                               # Next.js frontend (Phase 4)
└── scripts/                           # Setup, seed, pre-commit
```

---

## Documentation

### Implementation & Product

| Document | Description |
|----------|-------------|
| **[Implementation Status](docs/IMPLEMENTATION_STATUS.md)** | **What is built in this repo (update with each feature)** |
| [Product Vision](docs/product/PRODUCT-VISION.md) | Mission, users, differentiators |
| [Epics Overview](docs/product/EPICS-OVERVIEW.md) | 12 epics, ~120 user stories |
| [Release Plan](docs/product/releases/RELEASE-PLAN.md) | Alpha → Beta → v1.0 roadmap |

### Architecture & Design

| Document | Description |
|----------|-------------|
| [High-Level Architecture](docs/architecture/high-level-architecture.md) | Target system design |
| [ADR Index](docs/adr/README.md) | 10 Architecture Decision Records |
| [API Contracts](docs/design/api-contracts.md) | REST API + WebSocket specs |
| [LLD Index](docs/lld/README.md) | Design patterns, data models, search pipeline |

### Deep-Dives (Interview-Ready)

| Chapter | Topic | Priority |
|---------|-------|----------|
| [01](docs/deep-dives/01-tree-sitter-internals.md) | Tree-sitter Internals & AST Parsing | ⭐⭐⭐ |
| [02](docs/deep-dives/02-embedding-models-compared.md) | Embedding Models for Code | ⭐⭐ |
| [03](docs/deep-dives/03-hybrid-search-mechanics.md) | Hybrid Search & RRF Mechanics | ⭐⭐⭐ |
| [04](docs/deep-dives/04-pdf-layout-analysis.md) | PDF Layout Analysis | ⭐⭐ |
| [05](docs/deep-dives/05-rag-evaluation-science.md) | RAG Evaluation Science | ⭐⭐⭐ |

### Evaluation

| Document | Description |
|----------|-------------|
| [Evaluation README](docs/evaluation/README.md) | Methodology overview |
| [Metrics](docs/evaluation/metrics.md) | RAGAS metric definitions |
| [Baseline](docs/evaluation/baseline.md) | Naive vs. AST chunking comparison |

---

## Project Status

```
Documentation (architecture, ADRs, product, LLD)  ████████████████████ 100%
Engineering foundation (pyproject, CI, Docker)     ████████████████████ 100%
Core pipeline (ingestion → embedding → search)     ██░░░░░░░░░░░░░░░░░░  ~9%
RAG generation (context → LLM → citations)         ░░░░░░░░░░░░░░░░░░░░   0%
Frontend UI (Next.js + Monaco)                     ░░░░░░░░░░░░░░░░░░░░   0%
Evaluation & benchmarks                            ░░░░░░░░░░░░░░░░░░░░   0%
```

Details: **[docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md)**

---

## Connected Projects

| Project | Description | Relationship |
|---------|-------------|-------------|
| **[Pravah (प्रवाह)](https://github.com/Abhishekkumar2021/Pravah)** | Workflow orchestration platform for data pipelines | Drishti indexes Pravah's codebase as its demo. *The flow of data, and the vision to understand it.* |

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| AST parsing | Tree-sitter over regex | Multi-language, incremental, preserves code semantics |
| Vector DB | Qdrant over Pinecone/Chroma | Native hybrid search, self-hosted, payload filtering |
| Search | Hybrid BM25+Vector over pure vector | Exact keyword match + semantic understanding |
| Ranking | RRF over linear combination | Parameter-free fusion, robust across domains |
| Re-ranking | Cohere over cross-encoder | Production API quality, free tier available |
| PDF parsing | PyMuPDF over PyPDF2 | Layout-aware, tables, images, 10x faster |

See the [ADR Index](docs/adr/README.md) for all 10 decisions with context and trade-offs.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch strategy, PR workflow, and code quality requirements.

Run `make pre-commit` before every commit.

---

<div align="center">

Built as a serious engineering study — every design decision is intentional, documented, and interview-ready.

**[Implementation Status](docs/IMPLEMENTATION_STATUS.md) · [Architecture](docs/architecture/high-level-architecture.md) · [ADRs](docs/adr/README.md) · [Product](docs/product/README.md) · [LLD](docs/lld/README.md) · [Deep-Dives](docs/deep-dives/README.md)**

</div>
