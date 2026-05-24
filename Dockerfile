# ──────────────────────────────────────────────
# Drishti — दृष्टि
# Multi-stage Docker build
# ──────────────────────────────────────────────

# ═══ Stage 1: Builder ═════════════════════════
FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN uv venv /app/.venv && \
    uv sync --frozen --no-dev --python /app/.venv/bin/python

# ═══ Stage 2: Runtime ═════════════════════════
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY pyproject.toml README.md ./

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

RUN groupadd -r drishti && useradd -r -g drishti drishti
USER drishti

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "drishti.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
