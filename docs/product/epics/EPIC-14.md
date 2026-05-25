# EPIC-14: LangGraph Agent Runtime

**Priority:** P0 (V2) · **Status:** In Progress · **Depends on:** EPIC-15 (Postgres checkpointer)

## Objective

Replace the linear RAG path with a **LangGraph** agent that plans, retrieves, grades, optionally expands queries, generates with citations, and persists turns — competitive quality on hard engineering questions.

## User Stories

### US-14.01: Core agent graph
- [x] Compile graph with nodes: retrieve → generate → grade (retry loop)
- [x] `AgentRunner` is the sole Q&A path (no legacy linear ask)
- [x] Unit tests with mocked LLM and retriever

### US-14.02: LangChain tools
- [ ] `hybrid_search` wrapping `HybridSearchPipeline`
- [ ] `read_source` wrapping source read API
- [ ] `ingest_status` for workspace job state

### US-14.03: Postgres checkpointer
- [ ] `langgraph-checkpoint-postgres` integration
- [ ] Resume conversation after API restart

### US-14.04: Streaming SSE compatibility
- [ ] Map `astream_events` to existing SSE events (`token`, `citation`, `context`, `done`)
- [ ] No breaking changes to Next.js client

### US-14.05: Retrieval grader loop
- [ ] If grade fails, `expand_query` node (max 2 iterations)
- [ ] Log grader decisions for EPIC-11 eval

### US-14.06: Graph tool (EPIC-09 dependency)
- [ ] `graph_impact` tool when Neo4j enabled
- [ ] Router intent classifies “impact analysis” queries

## Acceptance

- Golden set: LangGraph path ≥ linear RAG on RAGAS faithfulness (EPIC-11)
- p95 first token &lt; 2s on dev hardware (Ollama small model exempt)

## References

- [Platform V2 Architecture](../../architecture/platform-v2-agentic.md)
- [ADR-011](../../adr/ADR-011-langgraph-agent-orchestration.md)
