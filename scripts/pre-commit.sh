#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🔎 Running pre-commit validation checks..."

# Check formatting and linting
echo "🧹 Running ruff checks..."
uv run ruff check .
uv run ruff format --check .

# Check type safety
echo "🛡️ Running type checks (mypy)..."
uv run mypy src/ tests/

# Run unit tests
echo "🧪 Running unit tests..."
uv run pytest tests/unit/

echo "✅ All pre-commit checks passed!"
exit 0
