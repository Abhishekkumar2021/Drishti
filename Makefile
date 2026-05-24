# ──────────────────────────────────────────────────────────
# Drishti — दृष्टि
# Multi-modal, AST-aware RAG system
# ──────────────────────────────────────────────────────────
#
# Usage:
#   make help          Show all available targets
#   make setup         First-time setup
#   make dev           Start development server
#   make test          Run all tests
#   make pre-commit    Full quality check before committing
# ──────────────────────────────────────────────────────────

.PHONY: help setup dev test test-unit test-integration test-e2e lint lint-fix type-check \
        docker-up docker-down docker-logs seed benchmark clean pre-commit

.DEFAULT_GOAL := help

# ═══════════════════════════════════════
# Setup
# ═══════════════════════════════════════

setup: ## First-time project setup
	@echo "🔮 Setting up Drishti..."
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	uv venv
	uv pip install -e ".[dev,eval]"
	@test -f .env || cp .env.example .env
	@echo ""
	@echo "✅ Setup complete!"
	@echo "   1. Edit .env with your API keys"
	@echo "   2. Run 'make docker-up' to start infrastructure"
	@echo "   3. Run 'make dev' to start the API server"

# ═══════════════════════════════════════
# Development
# ═══════════════════════════════════════

dev: ## Start FastAPI development server with hot reload
	uv run uvicorn drishti.main:app --reload --host 0.0.0.0 --port 8000

dev-web: ## Start Next.js frontend dev server (EPIC-10 — not yet implemented)
	@echo "Frontend (web/) is planned in EPIC-10 and is not available yet."
	@exit 1

# ═══════════════════════════════════════
# Testing
# ═══════════════════════════════════════

test: ## Run all tests
	uv run pytest tests/ -v --cov=src/drishti --cov-report=term-missing

test-unit: ## Run unit tests only (no external dependencies)
	uv run pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests (requires Docker services)
	uv run pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests (full pipeline)
	uv run pytest tests/e2e/ -v -m e2e

# ═══════════════════════════════════════
# Code Quality
# ═══════════════════════════════════════

lint: ## Check code style and quality
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

lint-fix: ## Auto-fix lint issues and format code
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

type-check: ## Run mypy type checking
	uv run mypy src/

# ═══════════════════════════════════════
# Docker Infrastructure
# ═══════════════════════════════════════

docker-up: ## Start infrastructure (Qdrant, Redis)
	docker compose up -d
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 3
	@docker compose ps
	@echo ""
	@echo "✅ Infrastructure ready!"
	@echo "   Qdrant:  http://localhost:6333/dashboard"
	@echo "   Redis:   localhost:6379"

docker-down: ## Stop infrastructure
	docker compose down

docker-logs: ## Tail infrastructure logs
	docker compose logs -f

docker-clean: ## Stop infrastructure and delete volumes
	docker compose down -v

# ═══════════════════════════════════════
# Data & Evaluation
# ═══════════════════════════════════════

seed: ## Index sample codebase for demo
	uv run python scripts/seed.py

benchmark: ## Run RAG evaluation benchmarks (EPIC-11 — not yet implemented)
	@echo "Benchmark scripts are planned in EPIC-11. See benchmarks/README.md."
	@exit 1

# ═══════════════════════════════════════
# Pre-Commit Workflow
# ═══════════════════════════════════════

pre-commit: lint type-check test-unit ## Full quality check (lint + types + unit tests)
	@echo ""
	@echo "══════════════════════════════════════"
	@echo "  ✅ All pre-commit checks passed!"
	@echo "  Safe to commit."
	@echo "══════════════════════════════════════"

# ═══════════════════════════════════════
# Cleanup
# ═══════════════════════════════════════

clean: ## Remove build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage
	@echo "🧹 Cleaned!"

# ═══════════════════════════════════════
# Help
# ═══════════════════════════════════════

help: ## Show this help message
	@echo ""
	@echo "  Drishti (दृष्टि) — Development Commands"
	@echo "  ════════════════════════════════════════"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
