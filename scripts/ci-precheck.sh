#!/usr/bin/env bash
# Run the same checks as GitHub Actions before opening a PR.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "══════════════════════════════════════════════════════════════"
echo "  Drishti CI precheck (parity with GitHub Actions)"
echo "══════════════════════════════════════════════════════════════"

echo ""
echo "▶ Sync dependencies (frozen, dev + eval — matches Python · Tests)"
uv sync --frozen --extra dev --extra eval

echo ""
echo "▶ Python · Code quality — ruff"
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/

echo ""
echo "▶ Python · Code quality — mypy"
uv run mypy src/

echo ""
echo "▶ Python · Tests — unit + coverage ≥70%"
uv run pytest tests/unit/ -v -m unit \
  --cov=src/drishti \
  --cov-report=xml \
  --cov-report=term-missing \
  --cov-fail-under=70

echo ""
echo "▶ Security · Bandit"
uv run bandit -r src/drishti -c pyproject.toml

echo ""
echo "▶ Security · pip-audit (dev dependencies only)"
uv sync --frozen --extra dev
uv run pip-audit

echo ""
echo "▶ Docker · Build"
docker build -t drishti:ci-precheck .
docker run --rm drishti:ci-precheck python -c "from drishti import __version__; print(f'Drishti v{__version__}')"

echo ""
echo "▶ Python · Integration tests"
if bash scripts/wait-for-services.sh; then
  uv run pytest tests/integration/ -v -m integration --tb=short
else
  echo "⚠️  Skipping integration tests — start services with: make docker-up"
  exit 1
fi

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  ✅ All CI prechecks passed — safe to open/update PR"
echo "══════════════════════════════════════════════════════════════"
