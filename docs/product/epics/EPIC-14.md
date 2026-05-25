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
- [x] `hybrid_search` wrapping `HybridSearchPipeline` — `agent/tools/search.py`
- [x] `read_source` wrapping source read API — `agent/tools/source.py`
- [x] `ingest_status` for workspace job state — `agent/tools/ingest.py`
- [x] Optional `tools` graph node (LLM JSON router invokes one tool before retrieve)

### US-14.03: Postgres checkpointer
- [x] `langgraph-checkpoint-postgres` integration — `agent/checkpointer.py`
- [x] Thread ID = conversation ID on `/conversations/{id}/ask`
- [ ] Resume conversation after API restart (requires streaming via graph — US-14.04)

### US-14.04: Streaming SSE compatibility
- [x] Map LangGraph `astream` (`updates` + `custom`) to existing SSE events (`token`, `citation`, `context`, `done`)
- [x] No breaking changes to Next.js client (async `ask_stream`)

### US-14.05: Retrieval grader loop
- [x] If grade fails, `expand_query` node (max 2 iterations) — `agent/nodes.py`, `agent/graph.py`
- [x] Log grader decisions for EPIC-11 eval (`agent_grade_retry`, `agent_query_expanded`)

### US-14.06: Graph tool (EPIC-09 dependency)
- [ ] `graph_impact` tool when Neo4j enabled
- [ ] Router intent classifies “impact analysis” queries

## Acceptance

- Golden set: LangGraph path ≥ linear RAG on RAGAS faithfulness (EPIC-11)
- p95 first token &lt; 2s on dev hardware (Ollama small model exempt)

## References

- [Platform V2 Architecture](../../architecture/platform-v2-agentic.md)
- [ADR-011](../../adr/ADR-011-langgraph-agent-orchestration.md)
