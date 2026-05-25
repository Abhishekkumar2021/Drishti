#!/usr/bin/env bash
# One-shot local dev bootstrap: Docker infra, Ollama models, .env sanity, service wait.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

EMBED_MODEL="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
CHAT_MODEL="${OLLAMA_CHAT_MODEL:-llama3.2}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"

echo "🔮 Drishti dev-ready"
echo ""

if [ ! -f .env ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
  echo "⚠️  Edit .env if needed — local profile uses Ollama (see .env.example)."
fi

if grep -q '^LLM_PROVIDER=mock' .env 2>/dev/null; then
  echo "⚠️  .env has LLM_PROVIDER=mock — chat returns a fixed stub, not real answers."
  echo "   Change to LLM_PROVIDER=ollama (see .env.example local profile)."
fi

echo "▶ Starting Docker (Qdrant, Redis, Ollama)..."
if ! docker compose up -d 2>&1; then
  echo "⚠️  docker compose reported an error (e.g. port 6379 already in use)."
  echo "   Continuing if Qdrant/Redis/Ollama are already reachable..."
fi
sleep 2
bash scripts/docker-ollama-pull.sh

echo ""
echo "▶ Waiting for Qdrant, Redis, Ollama (${EMBED_MODEL} + ${CHAT_MODEL})..."
export WAIT_OLLAMA=1
export OLLAMA_CHAT_MODEL="${CHAT_MODEL}"
bash scripts/wait-for-services.sh

echo ""
echo "▶ Provider check (from .env)..."
if command -v uv >/dev/null 2>&1; then
  uv run python - <<'PY' 2>/dev/null || true
from drishti.config import get_settings

s = get_settings()
print(f"  embedding: {s.embedding_provider} / {s.resolved_embedding_model()}")
print(f"  llm:       {s.llm_provider} / {s.resolved_llm_model()}")
if s.llm_provider == "mock":
    print("  ⚠️  LLM is mock — set LLM_PROVIDER=ollama in .env and restart make dev")
PY
fi

echo ""
echo "✅ Ready to test. In two terminals:"
echo "   Terminal 1:  make dev          # API http://localhost:8000"
echo "   Terminal 2:  make dev-web       # UI  http://localhost:3000"
echo ""
echo "Then: connect a repo → Index → ask in chat."
echo "Scope: code AST only today (.py, .java, .js/.ts, .go). PDF/Markdown → docs/SCOPE.md"
