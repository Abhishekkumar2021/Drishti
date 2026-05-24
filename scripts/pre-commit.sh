#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "Running pre-commit validation checks..."

echo "Running ruff checks..."
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/

echo "Running type checks (mypy)..."
uv run mypy src/

echo "Running unit tests..."
uv run pytest tests/unit/ -m unit --cov=src/drishti --cov-fail-under=70

echo "All pre-commit checks passed."
