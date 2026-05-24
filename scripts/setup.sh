#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting Drishti setup..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ 'uv' package manager is not installed. Please install it first: https://github.com/astral-sh/uv"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "⚠️ Warning: 'docker' command not found. You will need Docker to run Qdrant and Redis."
else
    echo "✅ Docker is installed."
fi

# Setup Python virtual environment and dependencies
echo "📦 Installing project dependencies..."
uv sync

# Create env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from template .env.example..."
    cp .env.example .env
    echo "⚠️ Please edit your .env file to include your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)."
fi

# Link git hooks
echo "⚓ Setting up Git pre-commit hooks..."
if [ -d .git ]; then
    cp scripts/pre-commit.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✅ Git hooks linked successfully."
else
    echo "⚠️ Warning: Not a git repository. Skipping hook installation."
fi

echo "🎉 Drishti setup completed successfully!"
echo "Run 'make dev' to start local databases and serve the FastAPI application."
