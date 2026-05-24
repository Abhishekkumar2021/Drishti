# Low-Level Design (LLD): Drishti (दृष्टि)

This directory contains the Low-Level Design (LLD) documentation for the core services and pipelines in Drishti. These files describe class structures, schemas, algorithms, and design patterns.

---

## LLD Index & Interview Priority

For engineers reviewing this repository for technical interviews, we have ranked our design documents by relevancy to core software engineering concepts:

| Chapter | Topic | Interview Relevance | Key Coding Concepts Covered |
|---------|-------|---------------------|-----------------------------|
| **[LLD Chapter 03](file:///Users/abhishek/Dev/Drishti/docs/lld/03-chunking-strategies.md)** | AST Chunking Strategies | 🔥 **High (Must Read)** | Abstract Syntax Tree traversal, language parsing algorithms, Tree-sitter query integration. |
| **[LLD Chapter 04](file:///Users/abhishek/Dev/Drishti/docs/lld/04-search-pipeline.md)** | Hybrid Search Pipeline | 🔥 **High (Must Read)** | Reciprocal Rank Fusion (RRF) math, cross-encoders, query expansion, caching. |
| **[LLD Chapter 02](file:///Users/abhishek/Dev/Drishti/docs/lld/02-data-models.md)** | Data Models & Vector Schemas | ⚡ **Medium** | Pydantic validation schemas, Qdrant payload filters, Neo4j dependency schemas. |
| **[LLD Chapter 01](file:///Users/abhishek/Dev/Drishti/docs/lld/01-design-patterns.md)** | Design Patterns Catalog | ⚡ **Medium** | Registry Pattern, Factory Pattern, Strategy Pattern, Observer/SSE patterns. |
| **[LLD Chapter 05](file:///Users/abhishek/Dev/Drishti/docs/lld/05-evaluation-framework.md)** | Evaluation Framework | ❄️ **Low** | RAGAS metrics, golden dataset compilation, benchmark orchestration. |

---

## Key LLD Objectives

1. **Production Blueprint**: Provides exact class interfaces and signatures so developers can implement features with zero ambiguity.
2. **Pedagogical Asset**: Explains not just *what* class structures are used, but *why* they fit standard object-oriented and functional programming paradigms.
3. **Auditability**: Maps directly back to our approved [ADRs](file:///Users/abhishek/Dev/Drishti/docs/adr/README.md) and [Product Epics](file:///Users/abhishek/Dev/Drishti/docs/product/EPICS-OVERVIEW.md).

**Companion architecture docs:** [C4 model](../architecture/c4-model.md) · [As-built ingestion](../architecture/as-built-code-ingestion.md) · [Universal Chunk schema](../design/universal-chunk-schema.md)
