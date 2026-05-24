# GitHub Actions

| Workflow | File | When it runs | Purpose |
|----------|------|--------------|---------|
| **Python CI** | `ci.yml` | PR/push to `main`/`develop` (Python paths) | Ruff lint/format, mypy, unit tests with coverage gate, Docker build |
| **Integration CI** | `integration-ci.yml` | PR/push (integration paths) | Qdrant + Redis service containers, health + storage tests |
| **Security** | `security.yml` | PR/push + weekly | Bandit SAST, pip-audit dependency scan |
| **Pull Request** | `pull-request.yml` | Every PR to `main`/`develop` | Conventional title, doc link check, size guard |

## Required status checks (branch protection)

After enabling branch protection on `develop`, prefer these **job names**:

**Python changes**

- `Python · Code quality`
- `Python · Tests`
- `Docker · Build`
- `Security · Bandit (SAST)`
- `Security · pip-audit`
- `Python · Integration tests` (when integration paths change)

**All PRs**

- `PR · Conventional title`

Remove stale entries such as `Code Quality`, `Tests`, or `Docker Build` from older workflow versions.

## Local parity

```bash
make pre-commit          # fast: lint + types + unit tests (no Docker)
make ci-precheck         # full GitHub Actions parity before opening a PR
make docker-up           # start Qdrant + Redis locally
make test-integration    # integration tests only (waits for services)
# or
./scripts/pre-commit.sh
./scripts/ci-precheck.sh
```
