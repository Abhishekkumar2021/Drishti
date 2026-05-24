# ADR-009: Redis Caching

## Context & Problem Statement
Running LLM Q&A calls on every query is costly and time-consuming (~2-5 seconds). Recurring questions (e.g. on repository onboarding, standard setup queries) should be resolved instantly without hitting APIs. Additionally, we need to protect our FastAPI gateway from API spam.

## Decision
We select **Redis** for response caching and rate-limiting storage.

## Alternatives Considered
* **In-memory dictionary (Python dictionary)**: Simple but does not persist across application restarts, lacks automatic TTL expiration, and is not shared across multi-worker server deployments.
* **PostgreSQL / SQLite caching**: Slower read-write times compared to an in-memory key-value store.

## Consequences
* **Pros**:
  * Sub-millisecond cache lookups.
  * Native Key expiration (TTL) handles cache eviction automatically.
  * Acts as a fast database for rate-limit tokens.
* **Cons**:
  * Cache key invalidation requires coordination with the repository Git hash to ensure answers update when code changes.
