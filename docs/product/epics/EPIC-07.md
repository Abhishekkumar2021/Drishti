# EPIC-07: RAG Pipeline & Generation

This epic covers assembling context from search results, prompting the LLM, managing streaming outputs, and extracting citations.

---

## Epic Metadata
* **Complexity**: 42 Story Points
* **Priority**: P0 (Critical Blocker)
* **Status**: Planned

---

## User Stories

### US-07.01: Prompt template compiler & context builder
**As a** Drishti RAG Service  
**I want** to format retrieved code and text blocks into structured context envelopes  
**So that** the LLM understands file names, paths, lines, and relationships.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Assembles context using a system instructions template.
2. [ ] Wraps each context chunk in clear delimiters (e.g. `<context file="path" start="1" end="10">...</context>`).
3. [ ] Computes and limits token count to avoid context overflow.

---

### US-07.02: LLM client integration (Claude API)
**As a** Drishti Developer  
**I want** to configure a client for Claude 3.5 Sonnet  
**So that** we can get high-quality codebase explanations.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Configures anthropic-sdk client.
2. [ ] Configures temperature, max tokens, and system prompts.
3. [ ] Gracefully catches and reports API connectivity failures.

---

### US-07.03: Streaming response mechanism
**As a** Drishti User  
**I want** answers to stream in real-time as they are being generated  
**So that** I don't have to wait for the entire response to complete before reading.

**Complexity**: 13 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Server streams tokens via Server-Sent Events (SSE) or FastAPI StreamingResponse.
2. [ ] Connection cleanup is performed when the client terminates early.

---

### US-07.04: Citation parser & line reference generator
**As a** Software Engineer  
**I want** LLM responses to contain strict citations linking back to files and lines in the codebase  
**So that** I can verify the correctness of the answer.

**Complexity**: 13 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Prompt forces the LLM to output citations in a standardized format, e.g. `[src/auth.py:L10-15]`.
2. [ ] Backend validates that the cited files and lines actually exist in the retrieved context to prevent hallucination.
3. [ ] Parses citations into structured JSON references alongside the text tokens.
