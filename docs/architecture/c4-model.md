# C4 Model: Drishti

The [C4 model](https://c4model.com/) structures architecture documentation into four zoom levels. This document uses **Mermaid** diagrams so they render in GitHub, IDEs, and documentation portals without external tools.

---

## Level 1: System Context

Drishti sits between developers and organizational knowledge (codebases, specs, diagrams). External systems supply models, storage, and optional orchestration.

```mermaid
C4Context
    title System Context — Drishti

    Person(dev, "Developer / Tech Lead", "Asks questions about code and docs")
    Person(pm, "Product / Architect", "Reads cited answers and impact analysis")

    System(drishti, "Drishti", "AST-aware RAG: ingest, index, search, cite")

    System_Ext(openai, "OpenAI API", "Dense embeddings")
    System_Ext(anthropic, "Anthropic API", "Answer generation (Claude)")
    System_Ext(cohere, "Cohere API", "Re-ranking")
    System_Ext(qdrant, "Qdrant", "Vector + payload store")
    System_Ext(redis, "Redis", "Query cache")
    System_Ext(neo4j, "Neo4j", "Optional dependency graph")
    System_Ext(git, "Git / GitHub", "Source repositories")
    System_Ext(pravah, "Pravah", "Sister orchestration platform (demo corpus)")

    Rel(dev, drishti, "Search, Ask, Ingest")
    Rel(pm, drishti, "Read answers with citations")
    Rel(drishti, git, "Clone, diff, walk files")
    Rel(drishti, qdrant, "Upsert / query chunks")
    Rel(drishti, redis, "Cache retrieval results")
    Rel(drishti, openai, "Embed chunks & queries")
    Rel(drishti, anthropic, "Stream RAG answers")
    Rel(drishti, cohere, "Re-rank candidates")
    Rel(drishti, neo4j, "Graph traversal (planned)")
    Rel(drishti, pravah, "Indexes demo monorepo")
```

---

## Level 2: Container Diagram

Runtime containers in the **target** production layout. Shaded components are implemented today; dashed are planned.

```mermaid
flowchart TB
    subgraph clients [Clients]
        WEB[Next.js Web UI<br/>planned]
        CLI[HTTP Clients / IDE<br/>planned]
    end

    subgraph drishti_host [Drishti Host — FastAPI]
        API[API Gateway<br/>🟩 implemented]
        ING[Ingestion Workers<br/>🟨 parsers done, embed TBD]
        SRCH[Search Service<br/>🟩 library]
        GEN[Generation Service<br/>🟨 LLM factory]
    end

    subgraph data [Data Stores]
        QD[(Qdrant<br/>🟩 Docker / health)]
        RD[(Redis<br/>🟩 Docker / health)]
        N4J[(Neo4j<br/>🔮 optional)]
    end

    subgraph external [External APIs]
        OAI[OpenAI]
        ANT[Anthropic]
        COH[Cohere]
    end

    WEB --> API
    CLI --> API
    API --> ING
    API --> SRCH
    SRCH --> GEN
    ING --> QD
    ING --> N4J
    SRCH --> QD
    SRCH --> RD
    GEN --> ANT
    ING --> OAI
    SRCH --> OAI
    SRCH --> COH
```

| Container | Technology | Status |
|-----------|------------|--------|
| API Gateway | FastAPI + Uvicorn | Health, config, middleware, OpenAPI |
| Ingestion | Python package `drishti.ingestion` | Walker, parsers, chunk schema |
| Search / Generation | `drishti.search`, `drishti.generation` | Scaffolding only |
| Qdrant | Docker Compose | Integration-tested |
| Redis | Docker Compose | Integration-tested |

---

## Level 3: Component — Ingestion

Components inside the ingestion path that are **implemented** on `develop` (EPIC-03).

```mermaid
flowchart LR
    subgraph discovery [Discovery]
        FW[FileWalker]
        LR[LanguageRegistry]
        GI[GitignoreMatcher]
    end

    subgraph ast [AST Parsing]
        PR[ParserRegistry]
        CAT[PARSER_CATALOG]
        RULES[parser_rules.json]
        BASE[TreeSitterParser]
        PY[PythonParser]
        JV[JavaParser]
        JS[JavaScriptParser]
        TS[TypeScriptParser]
        GO[GoParser]
    end

    subgraph output [Output]
        UC[UniversalChunk list]
    end

    FW --> GI
    FW --> LR
    FW --> PR
    PR --> CAT
    CAT --> RULES
    CAT --> PY & JV & JS & TS & GO
    PY & JV & JS & TS & GO --> BASE
    BASE --> UC
```

### Responsibilities

| Component | Module | Responsibility |
|-----------|--------|----------------|
| `FileWalker` | `ingestion/walker.py` | Recursive repo scan, ignore rules, magic-byte detection |
| `LanguageRegistry` | `utils/language.py` | Extension + shebang → language id |
| `ParserRegistry` | `ingestion/base.py` | Extension → parser instance |
| `PARSER_CATALOG` | `ingestion/ast/catalog.py` | Production parser factories |
| `ParserRules` | `ingestion/ast/rules.py` | Query file + `min_chunk_lines` per language |
| `TreeSitterParser` | `ingestion/ast/base.py` | Query captures → `UniversalChunk` |

---

## Level 4: Code — Parser Parse Flow

```mermaid
sequenceDiagram
    participant P as TreeSitterParser
    participant TS as Tree-sitter
    participant Q as Query (.scm)
    participant M as Metadata enricher
    participant C as UniversalChunk

    P->>TS: parse(bytes)
    P->>Q: QueryCursor.matches(root)
    loop each capture
        P->>P: resolve symbol, span, decorators
        P->>P: apply min_chunk_lines filter
        P->>M: enrich (docstring, params, complexity)
        M->>C: build validated Pydantic model
    end
    P-->>P: sort by start_line
```

> **Note:** The metadata enricher step corresponds to US-03.07 (see [Universal Chunk Schema](../design/universal-chunk-schema.md) for field rollout).

---

## View Mapping

| Stakeholder question | Start here |
|---------------------|------------|
| What does Drishti connect to externally? | Level 1 |
| What do we deploy? | Level 2 + [deployment-topology.md](deployment-topology.md) |
| How does code become chunks? | Level 3 + [as-built-code-ingestion.md](as-built-code-ingestion.md) |
| What classes implement parsing? | Level 4 + [LLD Chapter 01](../lld/01-design-patterns.md) |
