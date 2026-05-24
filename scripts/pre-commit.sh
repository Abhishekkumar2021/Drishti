#!/usr/bin/env bash
# Fast local checks before commit (unit tests only; no Docker required).
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running pre-commit validation checks..."

echo "▶ Ruff (src, tests, scripts)"
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/

echo "▶ Mypy"
uv run mypy src/

echo "▶ Unit tests + coverage ≥70%"
uv run pytest tests/unit/ -m unit \
  --cov=src/drishti \
  --cov-report=term-missing \
  --cov-fail-under=70

echo ""
echo "✅ Pre-commit checks passed."
echo "   Before opening a PR, also run: make ci-precheck"
