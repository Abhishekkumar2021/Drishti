# Drishti (दृष्टि) Documentation Hub

Welcome to the documentation hub for **Drishti**, a multi-modal, AST-aware Retrieval-Augmented Generation (RAG) system for code and document understanding.

This documentation is designed to serve as a comprehensive, engineering-grade repository of our decisions, architecture, product requirements, and technical theory. It is structured to exceed industry standards and is used as a blueprint for our implementation.

---

## Documentation Directory Map

Drishti's documentation is divided into the following key domains. Each directory contains its own `README.md` introducing its contents:

| Directory / File | Description | Status | Target Audience |
|------------------|-------------|--------|-----------------|
| [product/](file:///Users/abhishek/Dev/Drishti/docs/product/README.md) | Product vision, release planning, epics overview, and detailed user stories. | 📖 Complete | Product Managers, Engineers |
| [architecture/](file:///Users/abhishek/Dev/Drishti/docs/architecture/high-level-architecture.md) | Target system architecture, component boundaries, and pipeline workflows. | 📖 Complete | Systems Architects, Devs |
| [design/api-contracts.md](file:///Users/abhishek/Dev/Drishti/docs/design/api-contracts.md) | Full API specifications (REST & WebSocket) and communication schemas. | 📖 Complete | Frontend/Backend Devs |
| [adr/](file:///Users/abhishek/Dev/Drishti/docs/adr/README.md) | Architecture Decision Records (ADRs 001–010) documenting technology choices. | 📖 Complete | Tech Leads, Devs |
| [rfc/](file:///Users/abhishek/Dev/Drishti/docs/rfc/README.md) | Request for Comments (RFC) template and process for proposed features. | 📖 Complete | Contributors |
| [lld/](file:///Users/abhishek/Dev/Drishti/docs/lld/README.md) | Low-Level Design (LLD) detailing design patterns, schemas, and pipelines. | 📖 Complete | Backend Engineers, Interviewers |
| [evaluation/](file:///Users/abhishek/Dev/Drishti/docs/evaluation/README.md) | Evaluation methodology, metrics (RAGAS), and retrieval benchmarks. | 📖 Complete | ML/RAG Engineers |
| [deep-dives/](file:///Users/abhishek/Dev/Drishti/docs/deep-dives/README.md) | Technical chapters explaining the underlying science (Tree-sitter, Hybrid Search, etc.). | 📖 Complete | ML/RAG Engineers, Interviewers |
| [model-card.md](file:///Users/abhishek/Dev/Drishti/docs/model-card.md) | Model card detailing AI models used, parameters, limits, and biases. | 📖 Complete | AI Compliance, ML Engineers |
| [IMPLEMENTATION_STATUS.md](file:///Users/abhishek/Dev/Drishti/docs/IMPLEMENTATION_STATUS.md) | Live source of truth tracking completed vs. planned user stories. | 📖 Complete | All Stakeholders |

---

## Connected Narrative: Pravah & Drishti

Drishti is designed as a sister project to [Pravah (प्रवाह)](https://github.com/Abhishekkumar2021/Pravah). 
* **Pravah** orchestrates the *flow* and synchronization of streaming data.
* **Drishti** provides the *vision* and comprehension to query and understand large codebases and documents.

Together, they represent a complete suite of high-performance, real-time data engineering and AI-driven knowledge retrieval.

---

## How to Navigating the Docs

If you are new to the codebase, we recommend the following reading order:
1. Start with the **[Product Vision](file:///Users/abhishek/Dev/Drishti/docs/product/PRODUCT-VISION.md)** to understand the "Why" and "Who".
2. Read the **[High-Level Architecture](file:///Users/abhishek/Dev/Drishti/docs/architecture/high-level-architecture.md)** to see "How" the pieces connect.
3. Browse the **[ADRs](file:///Users/abhishek/Dev/Drishti/docs/adr/README.md)** to understand our technology stack choices.
4. Read the **[Low-Level Design (LLD) Chapter 03](file:///Users/abhishek/Dev/Drishti/docs/lld/03-chunking-strategies.md)** to understand our core innovation: AST-aware chunking.
5. Refer to **[Implementation Status](file:///Users/abhishek/Dev/Drishti/docs/IMPLEMENTATION_STATUS.md)** to see which features are currently active or planned.
