# Contributing to Drishti

Thank you for your interest in contributing to Drishti! This document provides guidelines and instructions for contributing.

---

## Branch Strategy

```
main           ─────●──────────●──────────●──────
                    │          ▲           ▲
develop        ─────●──●───●───●──●───●───●──────
                       │       │      │
feature/...    ────────●───●───┘      │
                                      │
docs/...       ───────────────────●───┘
```

| Branch | Purpose | Merges Into |
|--------|---------|-------------|
| `main` | Production-ready releases | — (protected) |
| `develop` | Integration branch | `main` (via PR) |
| `feature/EPIC-NN-desc` | New features | `develop` |
| `docs/description` | Documentation only | `develop` |
| `fix/description` | Bug fixes | `develop` |

---

## Development Workflow

### 1. Fork & Clone

```bash
gh repo fork Abhishekkumar2021/Drishti --clone
cd Drishti
make setup
```

### 2. Create a Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/EPIC-03-python-parser
```

### 3. Develop

```bash
# Start infrastructure
make docker-up

# Start dev server
make dev

# Run tests as you go
make test-unit
```

### 4. Pre-Commit Checks

```bash
# Must pass before committing
make pre-commit
```

### 5. Submit PR

```bash
git push origin feature/EPIC-03-python-parser
gh pr create --base develop --title "feat(ingestion): add Python AST parser" --fill
```

---

## Code Quality Requirements

### Linting & Formatting

- **ruff** for linting and formatting (configured in `pyproject.toml`)
- Line length: **100 characters**
- Import sorting: **isort via ruff**

```bash
make lint       # Check
make lint-fix   # Auto-fix
```

### Type Checking

- **mypy** in strict mode
- Type hints required on all function signatures
- No `Any` without justification

```bash
make type-check
```

### Docstrings

- **Google-style** docstrings on all public functions, classes, and modules
- Include `Args`, `Returns`, `Raises` sections

---

## Pull Request Guidelines

### Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>
```

✅ Valid: `feat(ingestion): add Tree-sitter Python parser`
✅ Valid: `fix(search): handle empty query gracefully`
✅ Valid: `docs(adr): add ADR-002 for Tree-sitter`
❌ Invalid: `Update parser`
❌ Invalid: `fix stuff`

### PR Size

| Size | Lines Changed | Guidance |
|------|--------------|----------|
| 🟢 Small | < 200 | Ideal |
| 🟡 Medium | 200–500 | Acceptable |
| 🟠 Large | 500–1000 | Split if possible |
| 🔴 Too Large | > 1000 | Must split |

### PR Checklist

Every PR must fill out the [PR template](.github/PULL_REQUEST_TEMPLATE.md).

---

## Testing Requirements

| Change Type | Required Tests |
|-------------|---------------|
| New parser | Unit tests for node extraction, metadata enrichment |
| New API endpoint | Integration test with real/mock services |
| Search logic | Unit tests + evaluation benchmark comparison |
| Bug fix | Regression test proving the fix |
| Configuration | Test default values and overrides |

### Integration tests

Integration tests live in `tests/integration/` and require Qdrant and Redis:

```bash
make docker-up
make test-integration
```

CI runs them in `.github/workflows/integration-ci.yml` with service containers. Unit tests (`make pre-commit`) do not start Docker.

---

## Documentation

When contributing code, also update:

1. **Docstrings** on new public APIs
2. **IMPLEMENTATION_STATUS.md** if completing a user story
3. **CHANGELOG.md** under `[Unreleased]`
4. **ADR** if making an architectural decision
5. **Epic** acceptance criteria (check off completed items)

---

## Getting Help

- Open a [GitHub Issue](https://github.com/Abhishekkumar2021/Drishti/issues)
- Check existing [ADRs](docs/adr/README.md) for design rationale
- Read [Deep-Dives](docs/deep-dives/README.md) for technical understanding

---

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive experience for everyone.
