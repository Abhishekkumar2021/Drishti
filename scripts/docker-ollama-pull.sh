#!/usr/bin/env bash
# Wait for Ollama API, then pull embedding + chat models into drishti-ollama.
set -euo pipefail

EMBED_MODEL="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
CHAT_MODEL="${OLLAMA_CHAT_MODEL:-llama3.2}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
CONTAINER="${OLLAMA_CONTAINER:-drishti-ollama}"
MAX_ATTEMPTS="${OLLAMA_WAIT_ATTEMPTS:-90}"
SLEEP_SECONDS="${OLLAMA_WAIT_SLEEP:-2}"

pull_model() {
  local model="$1"
  if docker exec "${CONTAINER}" ollama list 2>/dev/null | grep -q "${model}"; then
    echo "  ${model} — already present"
    return 0
  fi
  echo "  Pulling ${model}..."
  docker exec "${CONTAINER}" ollama pull "${model}"
}

echo "Waiting for Ollama at ${OLLAMA_URL}..."
attempt=1
while [ "${attempt}" -le "${MAX_ATTEMPTS}" ]; do
  if curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    break
  fi
  if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER}"; then
    echo "Container ${CONTAINER} is not running. Run: docker compose up -d ollama" >&2
    exit 1
  fi
  echo "  attempt ${attempt}/${MAX_ATTEMPTS}..."
  attempt=$((attempt + 1))
  sleep "${SLEEP_SECONDS}"
done

if [ "${attempt}" -gt "${MAX_ATTEMPTS}" ]; then
  echo "Timed out waiting for Ollama at ${OLLAMA_URL}" >&2
  exit 1
fi

echo "Pulling models into ${CONTAINER}..."
pull_model "${EMBED_MODEL}"
pull_model "${CHAT_MODEL}"
echo "Done — Ollama ready at ${OLLAMA_URL} (${EMBED_MODEL} + ${CHAT_MODEL})"
