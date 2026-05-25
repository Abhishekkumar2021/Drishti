# EPIC-17: Product UX Parity

**Priority:** P1 (V2) · **Status:** Planned · **Depends on:** EPIC-14, EPIC-15

## Objective

Web UI comparable to modern assistants **for the code/docs use case**: threads, uploads, indexing progress, memory panel, model settings.

## User Stories

### US-17.01: Conversation sidebar
- [ ] List threads; rename; delete
- [ ] New chat per workspace

### US-17.02: Upload & ingest UX
- [ ] Drag-drop to MinIO-backed upload
- [ ] Progress bar from job SSE/WebSocket

### US-17.03: Memory panel
- [ ] View/edit workspace facts (from compaction job)
- [ ] Show “what the agent remembers”

### US-17.04: Source panel
- [ ] Retrieval sources per message (chunks used)
- [ ] Click citation → Monaco (existing US-10.04)

### US-17.05: Settings
- [ ] Model provider picker (Ollama / Anthropic / OpenAI)
- [ ] Workspace switcher

## Out of scope

- General web browsing, image generation, voice — not Drishti’s wedge
