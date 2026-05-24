# API Contracts: Drishti (दृष्टि)

This document contains the complete API specifications for the Drishti backend service. It details REST endpoint interfaces, Pydantic request/response schemas, WebSocket contracts, and streaming specifications.

---

## Table of Contents

1. [Global API Standards](#1-global-api-standards)
2. [Endpoints Overview](#2-endpoints-overview)
3. [REST Endpoint Specifications](#3-rest-endpoint-specifications)
4. [Streaming Q&A SSE Specification](#4-streaming-qa-sse-specification)
5. [Error Handling Responses](#5-error-handling-responses)

---

## 1. Global API Standards

All endpoints, except health checks, are prefixed with `/api/v1`. 

* **Default Content-Type**: `application/json` (unless specifying `text/event-stream` for Q&A streaming).
* **Date-Time Format**: ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`).
* **Authentication**: Token-based authentication using HTTP Bearer tokens in headers:
  ```http
  Authorization: Bearer <drishti_api_token>
  ```

---

## 2. Endpoints Overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| **GET** | `/health` | No | System health check (Liveness/Readiness probes). |
| **POST**| `/api/v1/ingest` | Yes | Triggers repository/document indexing. |
| **GET** | `/api/v1/ingest/status/{job_id}` | Yes | Retrieves ingestion status and statistics. |
| **POST**| `/api/v1/search` | Yes | Returns ranked semantic/keyword results. |
| **POST**| `/api/v1/ask` | Yes | Streams LLM answers with references via SSE. |
| **POST**| `/api/v1/impact-analysis` | Yes | Triggers static dependency tracing. |

---

## 3. REST Endpoint Specifications

### A. Health Check
* **Path**: `/health`
* **Method**: `GET`
* **Response**: `200 OK`
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-05-24T12:00:00Z",
    "services": {
      "qdrant": "connected",
      "redis": "connected",
      "neo4j": "connected"
    },
    "version": "0.1.0"
  }
  ```

---

### B. Ingest Repository / Document
* **Path**: `/api/v1/ingest`
* **Method**: `POST`
* **Request Payload**:
  ```json
  {
    "repo_path": "/Users/abhishek/Dev/SampleProject",
    "branch": "main",
    "recursive": true,
    "force_reindex": false,
    "indexing_rules": {
      "exclude_patterns": ["**/node_modules/**", "**/dist/**", "*.log"],
      "minimum_line_threshold": 3
    }
  }
  ```
* **Response Payload (`202 Accepted`)**:
  ```json
  {
    "job_id": "ingest_job_6f9a0c12-38d5-4e78-90ab-cf1234567890",
    "status": "queued",
    "created_at": "2026-05-24T12:05:00Z"
  }
  ```

---

### C. Ingestion Job Status
* **Path**: `/api/v1/ingest/status/{job_id}`
* **Method**: `GET`
* **Response Payload (`200 OK`)**:
  ```json
  {
    "job_id": "ingest_job_6f9a0c12-38d5-4e78-90ab-cf1234567890",
    "status": "processing",
    "progress": {
      "files_total": 450,
      "files_processed": 120,
      "percentage_complete": 26.6,
      "errors": []
    },
    "started_at": "2026-05-24T12:05:02Z",
    "completed_at": null
  }
  ```

---

### D. Hybrid Search
* **Path**: `/api/v1/search`
* **Method**: `POST`
* **Request Payload**:
  ```json
  {
    "query": "Where is token verification handled?",
    "filters": {
      "language": "python",
      "file_path_pattern": "src/auth/**",
      "content_type": "code"
    },
    "limit": 5,
    "rerank": true
  }
  ```
* **Response Payload (`200 OK`)**:
  ```json
  {
    "query": "Where is token verification handled?",
    "results": [
      {
        "chunk_id": "9a38ff12-cdab-4321-9876-0987654321fe",
        "file_path": "src/auth/token.py",
        "language": "python",
        "content_type": "code",
        "start_line": 25,
        "end_line": 40,
        "content": "def verify_access_token(token: str):\n    try:\n        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])\n        return payload\n    except PyJWTError:\n        raise CredentialsException()",
        "score": 0.942,
        "parent_class": null,
        "name": "verify_access_token",
        "node_type": "function_definition"
      }
    ]
  }
  ```

---

### E. Change Impact Analysis
* **Path**: `/api/v1/impact-analysis`
* **Method**: `POST`
* **Request Payload**:
  ```json
  {
    "file_path": "src/auth/token.py",
    "line_number": 26
  }
  ```
* **Response Payload (`200 OK`)**:
  ```json
  {
    "source_symbol": {
      "name": "verify_access_token",
      "node_type": "function_definition",
      "file_path": "src/auth/token.py"
    },
    "impacted_dependencies": [
      {
        "name": "AuthService",
        "node_type": "class_declaration",
        "file_path": "src/auth/service.py",
        "relationship_path": ["verify_access_token", "calls", "login_user", "calls", "AuthService"]
      },
      {
        "name": "UserController",
        "node_type": "class_declaration",
        "file_path": "src/api/user.py",
        "relationship_path": ["verify_access_token", "calls", "get_current_user", "calls", "UserController"]
      }
    ]
  }
  ```

---

## 4. Streaming Q&A SSE Specification

The Q&A endpoint `/api/v1/ask` streams its output using Server-Sent Events (SSE).

* **Path**: `/api/v1/ask`
* **Method**: `POST`
* **Headers**:
  * `Accept: text/event-stream`
  * `Cache-Control: no-cache`
  * `Connection: keep-alive`
* **Request Payload**:
  ```json
  {
    "question": "How is authentication handled in this project?",
    "conversation_history": [
      {"role": "user", "content": "Hi"},
      {"role": "assistant", "content": "Hello! How can I help you navigate the codebase?"}
    ],
    "filters": {
      "exclude_paths": ["tests/**"]
    }
  }
  ```

### SSE Stream Event Sequence

#### Event 1: Context Retrieved
* **Event Name**: `context`
* **Data**:
  ```json
  {
    "sources": [
      {
        "id": 1,
        "file_path": "src/auth/token.py",
        "start_line": 25,
        "end_line": 40
      }
    ]
  }
  ```

#### Event 2: Token Output (Repeated)
* **Event Name**: `token`
* **Data**:
  ```json
  {
    "text": "Authentication"
  }
  ```

#### Event 3: Citations Resolution
* **Event Name**: `citation`
* **Data**:
  ```json
  {
    "citation_tag": "[src/auth/token.py:L25-40]",
    "file_path": "src/auth/token.py",
    "start_line": 25,
    "end_line": 40
  }
  ```

#### Event 4: Stream Complete
* **Event Name**: `done`
* **Data**:
  ```json
  {
    "total_tokens": 124,
    "execution_time_ms": 1420
  }
  ```

---

## 5. Error Handling Responses

Drishti uses standard HTTP error codes accompanied by structured JSON error bodies:

### A. 400 Bad Request
Occurs when there is a malformed payload or missing required parameters:
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "The query parameter cannot be empty.",
    "details": []
  }
}
```

### B. 422 Unprocessable Entity (Validation Error)
Generated automatically by FastAPI/Pydantic when data fails schema validation:
```json
{
  "detail": [
    {
      "loc": ["body", "repo_path"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### C. 429 Too Many Requests
Returned by the rate-limiting middleware:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. You can make 20 requests per minute.",
    "retry_after_seconds": 12
  }
}
```

### D. 500 Internal Server Error
Returned when unexpected errors occur inside backend engines:
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An error occurred inside the Tree-sitter parsing engine.",
    "job_id": "ingest_job_6f9a0c12-38d5-4e78-90ab-cf1234567890"
  }
}
```
