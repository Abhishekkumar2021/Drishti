# Operations & Runbook

Day-2 operations for developers and SREs running Drishti locally or in CI.

---

## Quick Commands

| Task | Command |
|------|---------|
| First-time setup | `make setup` |
| Start infra | `make docker-up` |
| Run API | `make dev` → http://localhost:8000 |
| Unit tests | `make test-unit` |
| Full CI locally | `make ci-precheck` |
| Fast pre-commit | `make pre-commit` |
| Stop infra | `make docker-down` |

---

## Health Checks

```mermaid
flowchart LR
    LIVE[/health/live] --> UP[Process running]
    READY[/health/ready] --> Q[Qdrant OK?]
    READY --> R[Redis OK?]
```

| Probe | Depends on Qdrant/Redis | Use case |
|-------|------------------------|----------|
| Liveness | No | Kubernetes restart if process dead |
| Readiness | Yes | Route traffic only when deps healthy |

Integration tests: `tests/integration/test_health_probes.py`.

---

## CI Precheck Parity

`make ci-precheck` mirrors GitHub Actions:

1. `uv sync` (dev + eval extras)
2. Ruff lint + format check
3. Mypy on `src/drishti`
4. Pytest unit + coverage ≥70%
5. Bandit
6. pip-audit (dev deps only — eval extras excluded due to transitive CVEs)
7. Docker build
8. Integration tests (`scripts/wait-for-services.sh`)

**Before opening a PR:** run `make ci-precheck` and ensure PR title uses conventional commit form with **capitalized subject** (e.g. `feat(ingestion): Add …`).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Integration tests skip / fail connect | Qdrant or Redis not running | `make docker-up`, wait for healthy |
| `wait-for-services.sh` timeout | Ports blocked | Check 6333, 6379 not in use |
| Mypy import errors | Stale venv | `uv sync --frozen --all-extras` |
| Coverage below 70% | Missing tests on new code | Add unit tests under `tests/unit/` |
| pip-audit fails on eval extras | Known ragas transitive issues | CI audits dev only; same locally |

---

## Logs & Observability (Target)

| Signal | Mechanism | Status |
|--------|-----------|--------|
| Request tracing | `X-Request-ID` middleware | 🟩 |
| Structured logs | Python `logging` | 🟩 basic |
| Metrics | Prometheus endpoint | 🔮 planned |
| Ingestion job progress | SSE / webhook | 🔮 planned |

---

## Security Operations

- Rotate API keys in `.env` (never commit).
- Review `security.yml` and Dependabot alerts weekly.
- See [SECURITY.md](../../SECURITY.md) for disclosure process.

---

## Related

- [Deployment topology](../architecture/deployment-topology.md)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
