# EPIC-08: API & Backend Service

This epic covers exposing Drishti's ingestion, search, and Q&A pipelines via structured FastAPI endpoints.

---

## Epic Metadata
* **Complexity**: 34 Story Points
* **Priority**: P0 (Critical Blocker)
* **Status**: Completed

---

## User Stories

### US-08.01: FastAPI routing
**As a** Drishti Integrator  
**I want** dedicated API endpoints for ingesting data, searching vectors, asking questions, and health checks  
**So that** external applications can interface with the service.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] Exposes `/api/v1/ingest` (POST) to trigger repo/doc indexing.
2. [x] Exposes `/api/v1/search` (POST) for hybrid retrieval.
3. [x] Exposes `/api/v1/ask` (POST) for streaming Q&A.
4. [x] Exposes `/api/v1/health` (GET) for container orchestration health checks.

---

### US-08.02: Request validation via Pydantic
**As a** Backend Developer  
**I want** all incoming API payloads to be validated against strict schemas  
**So that** we prevent bad data or injection attempts from crashing the backend.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] Defines input models for search (query, filters, limit) and Q&A (query, history, filters).
2. [x] Returns explicit 422 validation errors with descriptive fields when inputs are incorrect.

---

### US-08.03: Redis cache configuration for queries
**As a** Performance Architect  
**I want** to cache identical Q&A responses in Redis  
**So that** repeated user questions are resolved instantly without invoking the LLM.

**Complexity**: 13 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] Computes hash of query, history, and source commit state to act as cache key.
2. [x] Stores generated markdown answers in Redis with a configurable TTL (Time to Live).
3. [x] Invalidates cache when the underlying repository source files change.

---

### US-08.04: Rate limiting middleware
**As a** System Administrator  
**I want** to rate-limit incoming API requests by IP address or client ID  
**So that** the service is protected from overload.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] Integrates a middleware to limit requests per minute.
2. [x] Returns a 429 Too Many Requests status when limits are breached.
3. [x] Uses Redis to persist rate limiting counters.
