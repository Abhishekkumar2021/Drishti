# ADR-012: PostgreSQL as system of record

**Status:** Proposed  
**Date:** 2026-05-25  

## Context

Today, workspace metadata is a JSON file under `~/.cache`, conversations live in Redis without relational integrity, and there is no multi-tenant user model. This blocks:

- Auth/RBAC and audit trails
- Durable conversation history with pagination
- Ingest job tracking and retries
- LangGraph Postgres checkpointer

## Decision

Use **PostgreSQL 16+** as the **system of record** for all platform metadata.

- **ORM:** SQLAlchemy 2.0 async + **Alembic** migrations
- **Driver:** `asyncpg`
- **Tenancy:** `organization_id` on all major tables; optional Row-Level Security later

### Core tables (initial)

- `organizations`, `users`, `memberships`
- `workspaces`, `artifacts`, `ingest_jobs`
- `conversations`, `messages`
- `workspace_memory_facts` (structured long-term memory)
- `api_keys`, `audit_events`

Qdrant remains the **chunk index** — not duplicated in PG except optional metadata pointers.

## Consequences

**Positive:** ACID, backups, standard ops, joins for admin UI  
**Negative:** Another service in docker-compose; migration effort from Redis/file store  

Redis **retained** for cache, rate limits, pub/sub — not authoritative for messages.

## Alternatives

| Alternative | Rejected because |
|-------------|------------------|
| Redis only | Poor querying, no durable relational model at scale |
| SQLite | Weak concurrent write story for multi-user server |
| MongoDB | Team relational bias; graph served by Neo4j separately |
