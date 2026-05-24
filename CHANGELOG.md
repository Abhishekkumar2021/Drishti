# Changelog

All notable changes to Drishti will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation structure (ADRs, epics, LLD, deep-dives)
- Product vision and release plan
- Architecture documentation suite: C4 model, as-built ingestion, sequence diagrams, deployment topology
- Design reference for Universal Chunk schema (field table, ER diagram)
- Onboarding guide and operations runbook

---

## [0.1.0] - 2025-05-24

### Added
- Project scaffold with Python 3.12 + FastAPI
- `pyproject.toml` with full dependency list and dev tooling (ruff, mypy, pytest)
- `Dockerfile` with multi-stage build and health check
- `docker-compose.yml` for local development (Qdrant, Redis)
- `Makefile` with setup, dev, test, lint, and pre-commit targets
- GitHub Actions CI pipeline (lint, test with Qdrant/Redis, Docker build)
- Issue templates (bug report, feature request) and PR template
- `README.md` with architecture diagram, tech stack, and quick start
- `AGENTS.md` — AI coding assistant guidelines
- `CONTRIBUTING.md` — branch strategy and PR workflow
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1
- `SECURITY.md` — vulnerability reporting process
- FastAPI application skeleton with health check endpoint
- Pydantic configuration management (`config.py`)
- Source package structure (`src/drishti/` with all submodules)
- Test directory structure (unit, integration, e2e)

[Unreleased]: https://github.com/Abhishekkumar2021/Drishti/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Abhishekkumar2021/Drishti/releases/tag/v0.1.0
