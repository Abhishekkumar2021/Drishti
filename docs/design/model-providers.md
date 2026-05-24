# Model Provider Configuration

Drishti is **provider-agnostic**: embedding, chat LLM, and reranking backends are selected via environment variables and resolved through factory functions. Defaults match our approved ADRs (OpenAI embeddings, Anthropic chat, Cohere rerank) but any supported provider can be swapped without code changes.

---

## Quick reference

| Capability | Env var | Supported values |
|------------|---------|------------------|
| Dense embeddings | `EMBEDDING_PROVIDER` | `openai`, `cohere`, `ollama`, `openai_compatible`, `hashing` |
| Embedding model | `EMBEDDING_MODEL` | Any model ID your provider accepts |
| Vector size | `EMBEDDING_DIMENSIONS` | Must match model (e.g. `1536`, `1024`) |
| Chat LLM | `LLM_PROVIDER` | `anthropic`, `openai`, `ollama`, `openai_compatible`, `mock` |
| Chat model | `LLM_MODEL` | Provider-specific model name |
| Re-ranking | `RERANK_PROVIDER` | `auto`, `cohere`, `lexical` |
| Override API key | `EMBEDDING_API_KEY`, `LLM_API_KEY` | Single key for any provider |

Legacy variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`, `OPENAI_EMBEDDING_MODEL`) remain supported when the new `*_MODEL` fields are empty.

---

## Embedding providers

### `openai` (default)

```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
OPENAI_API_KEY=sk-...
```

Uses the OpenAI embeddings API with batching, retries, and optional dimension reduction for `text-embedding-3-*` models.

### `cohere`

```bash
EMBEDDING_PROVIDER=cohere
EMBEDDING_MODEL=embed-english-v3.0
EMBEDDING_DIMENSIONS=1024
COHERE_API_KEY=...
```

### `ollama` (local)

```bash
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSIONS=768
EMBEDDING_API_BASE=http://localhost:11434
```

No API key required when Ollama runs locally.

### `openai_compatible` (vLLM, LiteLLM, Azure OpenAI, etc.)

```bash
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_API_BASE=http://localhost:8000/v1
EMBEDDING_MODEL=your-embed-model
EMBEDDING_DIMENSIONS=1536
EMBEDDING_API_KEY=optional
```

### `hashing` (tests / CI only)

Deterministic vectors for unit and integration tests without external APIs.

```bash
EMBEDDING_PROVIDER=hashing
EMBEDDING_DIMENSIONS=16
```

---

## LLM providers

Used for **query expansion** today; the same `create_chat_llm()` factory will power RAG generation (EPIC-07).

| Provider | Typical use |
|----------|----------------|
| `anthropic` | Default; Claude models |
| `openai` | GPT-4o family |
| `ollama` | Local Llama / Mistral |
| `openai_compatible` | Self-hosted OpenAI-compatible chat APIs |
| `mock` | Unit tests (returns canned JSON) |

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Rerank providers

| Provider | Behavior |
|----------|----------|
| `auto` | Cohere if `COHERE_API_KEY` is set; otherwise lexical overlap |
| `cohere` | Requires `COHERE_API_KEY`; uses `RERANK_MODEL` |
| `lexical` | No external API; token overlap scoring |

---

## Code integration

```python
from drishti.config import get_settings
from drishti.embedding.factory import create_dense_embedder
from drishti.generation.factory import create_chat_llm
from drishti.search.factory import build_hybrid_search_pipeline

settings = get_settings()
embedder = create_dense_embedder(settings)
llm = create_chat_llm(settings)
# pipeline = build_hybrid_search_pipeline(settings, client=qdrant, dense_embedder=embedder)
```

Factories live in:

- `src/drishti/embedding/factory.py` — `create_dense_embedder`
- `src/drishti/generation/factory.py` — `create_chat_llm`
- `src/drishti/search/factory.py` — `build_hybrid_search_pipeline`

---

## Production validation

On startup, `validate_runtime_configuration()` checks:

1. Provider names are in the allowed set.
2. `EMBEDDING_DIMENSIONS` is positive.
3. `openai_compatible` providers have `*_API_BASE` set.
4. When `DEBUG=false`, API keys are present for cloud embedding/LLM/rerank providers.

Failures raise `ConfigurationError` and prevent the app from starting in strict mode.

---

## Related docs

- [.env.example](../../.env.example) — copy-paste templates
- [ADR-003: OpenAI text-embedding-3-small](../adr/ADR-003-openai-text-embedding-3-small.md) — default dense model rationale
- [ADR-005: Cohere reranker](../adr/ADR-005-cohere-reranker.md)
- [ADR-006: Claude API generation](../adr/ADR-006-claude-api-generation.md)
- [LLD Ch. 04 — Search pipeline](../lld/04-search-pipeline.md)
