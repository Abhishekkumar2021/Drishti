# EPIC-16: Auth, RBAC & Observability

**Priority:** P1 (V2) · **Status:** Planned · **Depends on:** EPIC-15

## Objective

Multi-tenant security and operability matching enterprise expectations: OIDC login, workspace roles, audit logs, distributed tracing.

## User Stories

### US-16.01: OIDC authentication
- [ ] Google + GitHub providers (configurable)
- [ ] JWT session for API; refresh tokens in HttpOnly cookie (web)

### US-16.02: Workspace RBAC
- [ ] Roles: `owner`, `editor`, `viewer`
- [ ] Enforce on ingest, upload, ask, memory APIs

### US-16.03: API keys
- [ ] Service accounts per workspace for CI/CD integrations

### US-16.04: Observability
- [ ] OpenTelemetry traces (FastAPI + LangGraph spans)
- [ ] Optional LangSmith for agent debugging
- [ ] Structured JSON logs with `request_id`, `conversation_id`

### US-16.05: Audit log
- [ ] `audit_events` table: ingest, upload, memory update, admin actions
