# Product Vision: Drishti (दृष्टि)

*See through your entire codebase and documentation.*

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Problem Landscape](#2-the-problem-landscape)
3. [The Solution: Drishti](#3-the-solution-drishti)
4. [Target Personas](#4-target-personas)
5. [Key Differentiators](#5-key-differentiators)
6. [Core Use Cases](#6-core-use-cases)
7. [Product Scope: Out of Scope](#7-product-scope-out-of-scope)
8. [Success Metrics](#8-success-metrics)

---

## 1. Executive Summary

Modern software development occurs across two disconnected universes:
* **The Code Universe**: Rich, structured, syntactical syntax trees, classes, and methods.
* **The Knowledge Universe**: PDFs, markdown pages, architectural images, API specifications, and meeting notes.

Existing AI tools (like simple chatbots or basic RAG implementations) fail because they treat both code and documentation as raw, flat text files. They chunk code by raw token length, breaking functions in half, losing structural references, and failing to read the architecture diagrams or PDFs that explain *why* the code was written.

**Drishti (दृष्टि)** bridge this gap. It is a multi-modal, AST-aware Retrieval-Augmented Generation (RAG) platform that ingests, parses, embeds, and indexes whole repositories—including their associated documentation and visual assets—into a unified semantic knowledge base. It provides software engineers, architects, and product teams with a single natural language interface to query their entire product landscape.

---

## 2. The Problem Landscape

Developers waste up to 30% of their working hours searching for information across disjointed files and legacy wikis. The issues can be categorized into three pillars:

### A. Contextual Fragmentation
Technical documentation sits in Confluence, PDFs, or Markdown, while the code lives in GitHub. When a developer asks "How is authentication configured?", a standard system searches only the code (yielding raw syntax) or only the documentation (yielding text), failing to synthesize the two into a single source of truth.

### B. Naive Chunking of Code
Most code-search tools split files by line-counts or character limits (e.g., every 500 characters). This destroys code syntax, splitting a function declaration from its implementation body, or separating a class field from the methods that rely on it. The result is poor retrieval and hallucinated answers from LLMs.

### C. Visual Blind Spots
Software architecture is inherently visual, defined by UML, sequence, and system design diagrams. Standard text-based RAG engines ignore these assets entirely, leaving a critical piece of repository knowledge unindexed.

---

## 3. The Solution: Drishti

Drishti solves these problems through an advanced engineering pipeline:

```
┌────────────────────────────────────────────────────────┐
│                        DRISHTI                         │
├────────────────────────────────────────────────────────┤
│   AST-Aware Code        Layout-Aware PDF  Visual OCR   │
│   Parsing (Tree-sitter)  & OpenAPI Parsing  & Vision   │
└───────────┬─────────────────────┬──────────────┬───────┘
            │                     │              │
            ▼                     ▼              ▼
       ┌──────────────────────────────────────────────┐
       │     Unified Multi-Modal Semantic Index       │
       │           (Qdrant Dense & Sparse)            │
       └──────────────────────┬───────────────────────┘
                              ▼
       ┌──────────────────────────────────────────────┐
       │     Hybrid Search + Cohere Re-ranking        │
       └──────────────────────┬───────────────────────┘
                              ▼
       ┌──────────────────────────────────────────────┐
       │      Claude-Generated Streaming Answers      │
       │          with Exact File/Line Citations      │
       └──────────────────────────────────────────────┘
```

By mapping both code and prose to a **Universal Chunk Schema**, Drishti preserves relationships (parent-child class hierarchies, file dependencies) and combines them with semantic search signals.

---

## 4. Target Personas

Drishti is built for three primary user personas:

### Persona A: The Onboarding/New Engineer (Devon)
* **Goal**: Understand a large, legacy repository quickly.
* **Challenge**: Overwhelmed by thousands of files, lack of documentation, and undocumented design patterns.
* **How Drishti Helps**: Devon asks questions like *"Where is user registration handled, and what files are modified if I add a new field?"* Drishti returns the exact code blocks, the OpenAPI spec, and an explanation of the flow.

### Persona B: The Tech Lead & Architect (Sarah)
* **Goal**: Perform impact analysis, enforce code quality, and ensure security.
* **Challenge**: Manually reading code to trace dependency chains or verify if architectural specs match implementation.
* **How Drishti Helps**: Sarah asks *"Does the implementation of our rate limiter match the specification defined in our architecture design PDF?"* Drishti runs a hybrid retrieval across the codebase and the PDF design doc, presenting a comparative analysis.

### Persona C: The RAG Application Builder (Alex)
* **Goal**: Build custom internal tools that require deep repository context.
* **Challenge**: Off-the-shelf vector database search provides noisy, disjointed code snippets to the LLM context.
* **How Drishti Helps**: Alex uses Drishti's API endpoints (`/api/v1/search`, `/api/v1/ask`) to get highly-structured, context-enriched chunks, reducing developer-hours spent configuring custom pipelines.

---

## 5. Key Differentiators

Drishti sets itself apart from standard RAG implementations through four engineering innovations:

1. **AST-Aware Parsing**: Using Tree-sitter to parse code into abstract syntax trees, allowing chunking boundaries to align perfectly with functions, methods, classes, and structures.
2. **Layout-Aware Prose Parser**: Not just extracting raw text from PDFs, but preserving headers, tables, callouts, and page numbers.
3. **Multi-Modal Retrieval**: Utilizing vision-language models to convert flowcharts, block diagrams, and architecture images into dense semantic descriptions.
4. **Hybrid Search with Fusion**: Merging dense vector search (for semantic meaning) with sparse BM25 search (for exact keyword/class name matching) and passing the result through a cross-encoder re-ranker.

---

## 6. Core Use Cases

Drishti is designed to solve complex Q&A scenarios:
* **Contextual Onboarding**: *"Explain the project layout and how the database connection is initialized."*
* **API Inquiries**: *"Show me the OpenAPI endpoint for creating a user and the backend handler method that processes it."*
* **Dependency & Impact Analysis**: *"If I change the return signature of the token verification helper, what other services are affected?"*
* **Specification Compliance**: *"Where is the encryption protocol from section 4.2 of our Security Spec PDF implemented in the codebase?"*

---

## 7. Product Scope: Out of Scope

To prevent scope creep, Drishti maintains strict boundaries:
* **No Code Editing/Refactoring**: Drishti is a search and understanding engine. It does not rewrite or commit code back to the repository.
* **Not an IDE**: It does not replace VS Code or JetBrains, but integrates with them via APIs.
* **No Deployment Management**: It does not hook into CI/CD pipelines to build, containerize, or deploy applications.

---

## 8. Success Metrics

Drishti's effectiveness will be measured quantitatively:

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| **Retrieval Precision** | > 85% | RAGAS Context Precision evaluated against golden dataset |
| **Retrieval Recall** | > 90% | RAGAS Context Recall against Golden Q&A |
| **LLM Faithfulness** | > 95% | Answer validation against retrieved context |
| **Latency (First Token)** | < 1.5s | Server-side measurement of streaming response startup |
| **Indexing Throughput** | > 50 files/sec | Core pipeline ingestion speed test (Python + Java codebase) |
