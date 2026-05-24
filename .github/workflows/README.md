# GitHub Actions

| Workflow | File | When it runs | Purpose |
|----------|------|--------------|---------|
| **Python CI** | `ci.yml` | PR/push to `main`/`develop` (Python paths) | Ruff lint/format, mypy, unit tests with coverage, Docker build |
| **Integration CI** | `integration-ci.yml` | PR/push when integration tests exist | Qdrant + Redis service containers (disabled until tests land) |
| **Pull Request** | `pull-request.yml` | Every PR to `main`/`develop` | Conventional title, doc link check, size guard |

## Required status checks (branch protection)

After enabling branch protection on `develop`, prefer these **job names**:

**Python changes**

- `Python · Code quality`
- `Python · Tests`
- `Docker · Build`

**All PRs**

- `PR · Conventional title`

Remove stale entries such as `Code Quality`, `Tests`, or `Docker Build` from older workflow versions.

## Local parity

```bash
make pre-commit
# or
./scripts/pre-commit.sh
```
