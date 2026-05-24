#!/usr/bin/env bash
# Wait until Qdrant and Redis are reachable (local docker-compose or CI services).
set -euo pipefail

QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
MAX_ATTEMPTS="${WAIT_MAX_ATTEMPTS:-60}"
SLEEP_SECONDS="${WAIT_SLEEP_SECONDS:-2}"

echo "Waiting for Qdrant at ${QDRANT_HOST}:${QDRANT_PORT} and Redis at ${REDIS_URL}..."

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  qdrant_ok=0
  redis_ok=0

  if uv run python -c "
import socket
s = socket.socket()
s.settimeout(2)
s.connect(('${QDRANT_HOST}', int('${QDRANT_PORT}')))
s.close()
" 2>/dev/null; then
    qdrant_ok=1
  fi

  if uv run python -c "
import redis
r = redis.from_url('${REDIS_URL}')
r.ping()
" 2>/dev/null; then
    redis_ok=1
  fi

  if [ "$qdrant_ok" -eq 1 ] && [ "$redis_ok" -eq 1 ]; then
    echo "All services are ready."
    exit 0
  fi

  echo "Attempt ${attempt}/${MAX_ATTEMPTS}: qdrant=${qdrant_ok} redis=${redis_ok}"
  attempt=$((attempt + 1))
  sleep "$SLEEP_SECONDS"
done

echo "Timed out waiting for dependencies." >&2
exit 1
