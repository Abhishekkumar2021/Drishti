# ADR-001: FastAPI Backend Framework

## Status
Approved

## Context & Problem Statement
We need a high-performance, asynchronous web framework for Python to expose the ingestion, search, and streaming Q&A endpoints. The framework must support input validation, generate OpenAPI documentation automatically, and handle concurrent connections (especially for long-running streaming Server-Sent Events).

## Decision
We select **FastAPI** as the backend web framework.

## Alternatives Considered
* **Flask**: Lightweight but lacks native asynchronous support (`async/await`) and built-in Pydantic integration, making streaming SSE endpoints less efficient.
* **Django**: Feature-rich but overly heavy for a microservice design. Its ORM is not required, and configuring custom async streaming flows is complex compared to FastAPI.

## Consequences
* **Pros**:
  * Out-of-the-box support for `async/await` enables handling thousands of concurrent SSE connections.
  * Auto-generates interactive OpenAPI (Swagger) specs.
  * Pydantic integration simplifies request/response validation.
* **Cons**:
  * Asynchronous routing requires careful dependency injection management to prevent database connection leaks.
