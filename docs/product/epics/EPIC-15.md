# EPIC-15: Data Platform (PostgreSQL + MinIO)

**Priority:** P0 (V2) · **Status:** Planned

## Objective

Establish production **system of record** (PostgreSQL) and **object storage** (MinIO) so API and workers scale horizontally and artifacts are not local-disk bound.

## User Stories

### US-15.01: PostgreSQL + Alembic
- [ ] docker-compose `postgres` service
- [ ] SQLAlchemy async models + initial migration
- [ ] `organizations`, `users`, `workspaces`, `conversations`, `messages`

### US-15.02: Artifacts & ingest jobs
- [ ] `artifacts`, `ingest_jobs` tables with status machine (`pending` → `processing` → `indexed` / `failed`)
- [ ] API returns job id + poll URL

### US-15.03: MinIO integration
- [ ] docker-compose `minio` + console
- [ ] Upload path: presigned PUT or server-side stream to `raw/`
- [ ] Worker reads from MinIO for parsing

### US-15.04: Migrate EPIC-13 stores
- [ ] Dual-write conversations Redis → Postgres; cutover flag
- [ ] Workspace index JSON → Postgres `workspaces`

### US-15.05: Arq worker
- [ ] `drishti-worker` process: ingest jobs, memory compaction (stub)
- [ ] Redis as Arq broker (reuse existing Redis)

## References

- [ADR-012](../../adr/ADR-012-postgresql-system-of-record.md)
- [ADR-013](../../adr/ADR-013-minio-object-storage.md)
