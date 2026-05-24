# Drishti — AI Coding Assistant Guidelines

> **Core principle:** Documentation first, then code. Every feature starts with an ADR or RFC, then an epic update, then implementation.

---

## Before Writing Any Code

### Check Documentation First

| If you need to understand... | Read this |
|------------------------------|-----------|
| What Drishti does | [README.md](README.md) |
| What's built vs. planned | [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) |
| System architecture | [docs/architecture/high-level-architecture.md](docs/architecture/high-level-architecture.md) |
| Why a technology was chosen | [docs/adr/](docs/adr/README.md) |
| Design patterns in use | [docs/lld/01-design-patterns.md](docs/lld/01-design-patterns.md) |
| Data models & schemas | [docs/lld/02-data-models.md](docs/lld/02-data-models.md) |
| API contracts | [docs/design/api-contracts.md](docs/design/api-contracts.md) |
| Model providers (embedding/LLM) | [docs/design/model-providers.md](docs/design/model-providers.md) |
| User stories & acceptance criteria | [docs/product/epics/](docs/product/epics/) |
| Chunking strategies | [docs/lld/03-chunking-strategies.md](docs/lld/03-chunking-strategies.md) |
| Evaluation methodology | [docs/evaluation/README.md](docs/evaluation/README.md) |

### Understand the Context

1. **Read the relevant epic** — know what user stories you're implementing
2. **Read the relevant ADR** — understand *why* the technology was chosen
3. **Read the existing code** — follow established patterns
4. **Check IMPLEMENTATION_STATUS.md** — know what exists already

### Write Tests First

- Unit tests for new logic (`tests/unit/`)
- Integration tests for external dependencies (`tests/integration/`)
- Update golden Q&A dataset if search behavior changes (`benchmarks/datasets/`)

---

## Implementation Standards

### Python 3.12

- **Type hints everywhere** — no `Any` unless absolutely necessary
- **Pydantic models** for all data structures (not raw dicts)
- **async/await** for I/O operations (FastAPI, httpx, Qdrant client)
- **Google-style docstrings** on all public functions and classes
- **No mutable default arguments** — use `field(default_factory=...)`

```python
# ✅ Good
async def search_chunks(
    query: str,
    *,
    top_k: int = 10,
    language_filter: str | None = None,
) -> list[SearchResult]:
    """Search for code chunks matching the query.

    Args:
        query: Natural language search query.
        top_k: Maximum number of results to return.
        language_filter: Optional language filter (e.g., "python", "java").

    Returns:
        List of search results ranked by relevance.
    """
    ...

# ❌ Bad
def search(q, k=10, lang=None):
    ...
```

### FastAPI Patterns

- **Dependency injection** for settings, DB clients, services
- **Pydantic schemas** for request/response models (in `api/schemas.py`)
- **Router separation** — one file per resource (ingest, search, ask)
- **Background tasks** for long-running operations (ingestion)
- **SSE streaming** for real-time responses (via `sse-starlette`)

### Error Handling

- Use **custom exception classes** in a dedicated module
- Return **structured error responses** with error codes
- Log errors with **context** (request ID, query, parameters)

### Configuration

- All config via **environment variables** (see `config.py` and [model-providers.md](docs/design/model-providers.md))
- Use **Pydantic BaseSettings** — never read `os.environ` directly
- **Provider-agnostic models**: `EMBEDDING_PROVIDER`, `LLM_PROVIDER`, `RERANK_PROVIDER` — never hardcode a single vendor in feature code
- Use factories: `create_dense_embedder()`, `create_chat_llm()`, `build_hybrid_search_pipeline()`
- Defaults for local development; `validate_runtime_configuration()` enforces keys when `DEBUG=false`

---

## Testing Requirements

| Type | Location | External Deps | Run With |
|------|----------|---------------|----------|
| **Unit** | `tests/unit/` | None | `make test-unit` |
| **Integration** | `tests/integration/` | Qdrant, Redis | `make test-integration` |
| **E2E** | `tests/e2e/` | All services | `make test-e2e` |
| **Evaluation** | `benchmarks/` | All + API keys | `make benchmark` |

### Test conventions

- Use **pytest fixtures** for setup/teardown
- Use **pytest.mark** decorators: `@pytest.mark.unit`, `@pytest.mark.integration`
- **Mock external APIs** in unit tests (OpenAI, Cohere, Anthropic)
- **Use Testcontainers** for Qdrant in integration tests when possible
- **Assert specific behaviors**, not implementation details

---

## What NOT to Do

- ❌ Do NOT add dependencies without an ADR or discussion
- ❌ Do NOT use `print()` — use `logging` module
- ❌ Do NOT hardcode API keys, URLs, or configuration values
- ❌ Do NOT use raw dicts for data — use Pydantic models
- ❌ Do NOT skip type hints on function signatures
- ❌ Do NOT write functions longer than 50 lines — extract helpers
- ❌ Do NOT commit without running `make pre-commit`
- ❌ Do NOT modify `docs/IMPLEMENTATION_STATUS.md` without also updating the code (or vice versa)
- ❌ Do NOT ignore mypy errors — fix them or add targeted `# type: ignore[code]`

---

## Pre-Commit Workflow

```bash
# Run the full pre-commit check
make pre-commit

# This runs:
#   1. ruff check src/ tests/          (lint)
#   2. ruff format --check src/ tests/ (format check)
#   3. mypy src/                       (type check)
#   4. pytest tests/unit/              (unit tests)
```

### Self-Review Checklist

Before submitting a PR:

- [ ] Code follows project style (ruff passes)
- [ ] Type hints on all function signatures (mypy passes)
- [ ] Docstrings on all public APIs
- [ ] Unit tests for new logic
- [ ] No hardcoded values — uses config
- [ ] Error cases handled
- [ ] IMPLEMENTATION_STATUS.md updated if completing a user story
- [ ] CHANGELOG.md updated

---

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change (no feature/fix) |
| `test` | Adding/updating tests |
| `chore` | Build, CI, tooling |
| `perf` | Performance improvement |

### Examples

```
feat(ingestion): add Tree-sitter parser for Python

Implement PythonASTParser using tree-sitter-python grammar.
Extracts function_definition, class_definition, and import_statement nodes.

Closes EPIC-03, US-03.02
```

```
docs(adr): add ADR-002 for Tree-sitter AST parsing

Document decision to use Tree-sitter over language-specific parsers
for multi-language AST extraction.
```

---

## Quality Gates

### DO NOT COMMIT IF:

1. `make lint` fails
2. `make type-check` fails
3. `make test-unit` fails
4. You haven't updated documentation for your changes
5. You have `TODO` or `FIXME` without a linked issue

---

## Git Workflow

```
main          ─────●──────●──────●──────
                   │      ▲      ▲
develop       ─────●──●───●──●───●──────
                      │      │
feature/...   ────────●──●───┘
```

- **main**: Production-ready, protected
- **develop**: Integration branch
- **feature/EPIC-NN-description**: Feature branches from develop
- **docs/description**: Documentation-only branches
- **fix/description**: Bug fix branches

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.
