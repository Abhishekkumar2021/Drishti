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

.PHONY: help setup dev-ready dev dev-web test test-unit test-integration test-e2e lint lint-fix type-check \
        docker-up docker-ollama-up docker-ollama-pull docker-down docker-logs db-migrate worker seed benchmark clean pre-commit ci-precheck

.DEFAULT_GOAL := help

# ═══════════════════════════════════════
# Setup
# ═══════════════════════════════════════

dev-ready: ## Bootstrap Docker, Ollama models, wait for services
	@bash scripts/dev-ready.sh

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

dev-web: ## Start Next.js frontend dev server (port 3000)
	@test -d web/node_modules || (cd web && npm install)
	cd web && npm run dev

# ═══════════════════════════════════════
# Testing
# ═══════════════════════════════════════

test: ## Run all tests
	uv run pytest tests/ -v --cov=src/drishti --cov-report=term-missing

test-unit: ## Run unit tests only (no external dependencies)
	uv run pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests (requires Docker services)
	@bash scripts/wait-for-services.sh
	uv run pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests (full pipeline)
	uv run pytest tests/e2e/ -v -m e2e

# ═══════════════════════════════════════
# Code Quality
# ═══════════════════════════════════════

lint: ## Check code style and quality
	uv run ruff check src/ tests/ scripts/
	uv run ruff format --check src/ tests/ scripts/

lint-fix: ## Auto-fix lint issues and format code
	uv run ruff check --fix src/ tests/ scripts/
	uv run ruff format src/ tests/ scripts/

type-check: ## Run mypy type checking
	uv run mypy src/

# ═══════════════════════════════════════
# Docker Infrastructure
# ═══════════════════════════════════════

docker-up: ## Start infrastructure (Qdrant, Redis, Postgres, MinIO, Ollama)
	docker compose up -d
	@echo "⏳ Waiting for services..."
	@sleep 5
	@$(MAKE) docker-ollama-pull
	@docker compose ps
	@echo ""
	@echo "✅ Infrastructure ready!"
	@echo "   Qdrant:   http://localhost:6333/dashboard"
	@echo "   Redis:    localhost:6379"
	@echo "   Postgres: localhost:5432 (user drishti — set POSTGRES_PASSWORD in .env)"
	@echo "   MinIO:    http://localhost:9001 (set MINIO_ROOT_PASSWORD in .env)"
	@echo "   Ollama:   http://localhost:11434"

db-migrate: ## Apply Alembic migrations to PostgreSQL
	DATABASE_URL=$${DATABASE_URL:-postgresql+asyncpg://drishti@localhost:5432/drishti} \
		uv run alembic upgrade head

worker: ## Start Arq background worker (ingest jobs)
	uv run arq drishti.worker.settings.WorkerSettings

docker-ollama-up: ## Start Ollama and pull embedding + chat models
	docker compose up -d ollama
	@bash scripts/docker-ollama-pull.sh

docker-ollama-pull: ## Pull models into running Ollama container
	@bash scripts/docker-ollama-pull.sh

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

benchmark: ## Run full RAG evaluation (requires running API)
	@echo "🔬 Running Drishti RAG Evaluation..."
	uv run python -m benchmarks.runner --strategy ast
	@echo ""
	@echo "📊 Results saved to benchmarks/results/"

benchmark-quick: ## Run quick evaluation (10 questions)
	uv run python -m benchmarks.runner --strategy ast --max-questions 10

benchmark-retrieval: ## Run retrieval-only evaluation
	uv run python -m benchmarks.eval_retrieval

benchmark-generation: ## Run generation-only evaluation
	uv run python -m benchmarks.eval_generation

benchmark-compare: ## Compare AST vs Naive chunking (requires both reports)
	@echo "Comparing evaluation reports..."
	@if ls benchmarks/results/eval_ast_*.json 1>/dev/null 2>&1 && ls benchmarks/results/eval_naive_*.json 1>/dev/null 2>&1; then \
		uv run python -m benchmarks.compare \
			--ast-report "$$(ls -t benchmarks/results/eval_ast_*.json | head -1)" \
			--naive-report "$$(ls -t benchmarks/results/eval_naive_*.json | head -1)"; \
	else \
		echo "❌ Missing evaluation reports. Run 'make benchmark' with both strategies first."; \
		exit 1; \
	fi

# ═══════════════════════════════════════
# Pre-Commit Workflow
# ═══════════════════════════════════════

pre-commit: lint type-check test-unit ## Fast check before commit (no Docker)
	@echo ""
	@echo "══════════════════════════════════════"
	@echo "  ✅ All pre-commit checks passed!"
	@echo "  Before a PR, run: make ci-precheck"
	@echo "══════════════════════════════════════"

ci-precheck: ## Full CI parity (lint, tests, security, Docker, integration)
	@bash scripts/ci-precheck.sh

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
