# ──────────────────────────────────────────────
# Drishti — दृष्टि
# Multi-stage Docker build
# ──────────────────────────────────────────────

# ═══ Stage 1: Builder ═════════════════════════
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create venv and install dependencies (cached layer)
RUN uv venv /app/.venv && \
    uv sync --frozen --no-dev --python /app/.venv/bin/python

# Copy source code
COPY src/ ./src/

# ═══ Stage 2: Runtime ═════════════════════════
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source
COPY --from=builder /app/src /app/src
COPY pyproject.toml ./

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

# Non-root user for security
RUN groupadd -r drishti && useradd -r -g drishti drishti
USER drishti

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start the server
CMD ["uvicorn", "drishti.main:app", "--host", "0.0.0.0", "--port", "8000"]
