# ADR-013: MinIO for object storage

**Status:** Proposed  
**Date:** 2026-05-25  

## Context

Artifacts (PDFs, exports, cloned repo archives) are stored on local filesystem paths. This fails for:

- Horizontal scaling (multiple API/worker pods)
- Presigned browser uploads
- Lifecycle policies (expire temp uploads)
- Parity with S3/GCS in production

## Decision

Use **MinIO** (S3-compatible API) for all **blob** storage.

**Bucket layout:**

```
drishti/
  {workspace_id}/
    raw/{artifact_id}/{filename}
    repos/{clone_hash}/...
    exports/{conversation_id}.md
```

**Metadata** (filename, mime, size, status) in PostgreSQL `artifacts` table — MinIO holds bytes only.

**Client access:** Presigned PUT/GET URLs (time-limited) from API; workers use internal endpoint.

## Consequences

**Positive:** Cloud-native pattern; same code path for AWS S3 in prod (endpoint URL change)  
**Negative:** Extra service; must handle credentials rotation  

## Alternatives

| Alternative | Rejected because |
|-------------|------------------|
| Postgres BYTEA | Bad for large PDFs; bloats DB |
| Local disk only | Not production-grade |
| Direct AWS S3 only | Worse local dev; MinIO mirrors S3 API |
