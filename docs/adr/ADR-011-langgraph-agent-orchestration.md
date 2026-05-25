# ADR-011: LangGraph for agent orchestration

**Status:** Accepted  
**Date:** 2026-05-25  
**Deciders:** Engineering  

## Context

Drishti’s ask path is a **linear** pipeline: search → context → LLM → citations. Production assistants use **multi-step** reasoning: grade retrieval, rewrite queries, call tools, branch on intent. Hand-rolling this in FastAPI leads to unmaintainable `if/else` and weak testability.

We need:

- Stateful conversations with checkpoints and resume
- Tool calling (search, read file, graph query)
- Optional human-in-the-loop (approve ingest, clarify question)
- Observable steps for debugging and eval

## Decision

Adopt **LangGraph** as the orchestration layer for `/conversations/{id}/ask` and eventually `/ask`.

Use **LangChain** narrowly for:

- Tool definitions and retriever adapters
- Optional LangSmith tracing
- **Not** for document loading of source code (keep Tree-sitter ingestion)

Keep existing Drishti services as the implementation behind tools:

- `HybridSearchPipeline`
- `ContextBuilder` / citation validators
- `create_chat_llm` factory (provider-agnostic)

Persist graph state with **`langgraph-checkpoint-postgres`** (requires ADR-012).

## Consequences

**Positive**

- Industry-standard agent patterns (grade documents, query rewrite loops)
- Checkpoint/resume across restarts
- Clear graph diagrams for docs and interviews
- Easier to add Neo4j / MCP tools as nodes

**Negative**

- New dependencies and learning curve
- Latency may increase (+1–2 LLM calls for grading) — mitigate with fast models for graders
- Linear `RAGPipeline.ask()` removed; retrieval lives in `prepare_context()` only

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Raw FastAPI state machine | Reinvents LangGraph; poor checkpoint story |
| AutoGen / CrewAI | Heavier multi-agent abstraction; overkill for v1 agent |
| Pydantic AI only | Less mature graph persistence; team standardizing on LangChain ecosystem |
| Single-shot RAG forever | Fails on hard queries; not competitive |

## Implementation notes

- Graph lives in `src/drishti/agent/`; `AgentRunner` is the only `/ask` entry point
- `RAGPipeline` provides hybrid search + prompt assembly (`prepare_context`)
- Streaming mirrors the retrieve-grade loop then tokenizes via the same LLM
