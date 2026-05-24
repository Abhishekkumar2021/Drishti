# EPIC-01: Project Setup & Documentation

This epic covers the initial workspace initialization, development environment configurations, CI/CD templates, and baseline documentation required to kickstart Drishti.

---

## Epic Metadata
* **Complexity**: 21 Story Points
* **Priority**: P0 (Critical Blocker)
* **Status**: Completed

---

## User Stories

### US-01.01: Python structure + UV package manager
**As a** Drishti Backend Developer  
**I want** a standardized python environment initialized via `uv` and configured in `pyproject.toml`  
**So that** I have fast, repeatable builds with strict linting, formatting, and type-checking rules.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] Project initialized with Python 3.12 target.
2. [x] `pyproject.toml` contains dependencies for FastAPI, Qdrant, Pydantic, and dev tools (`ruff`, `mypy`, `pytest`).
3. [x] Dev environment setup commands are scriptable.

---

### US-01.02: Docker setup (Qdrant, Redis)
**As a** Drishti Infrastructure Engineer  
**I want** a local development environment running Qdrant and Redis in containers  
**So that** I can write tests and debug code against local instances without cloud dependencies.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] `docker-compose.yml` configures Qdrant (with dense+sparse enabled) and Redis.
2. [x] Dockerfile provides multi-stage caching, optimized for running the FastAPI application.
3. [x] Container health checks are defined and functional.

---

### US-01.03: GitHub Actions CI workflow setup
**As a** Drishti Maintainer  
**I want** pull requests to run automated test suites, type-checking, and formatting checks  
**So that** we maintain code quality and prevent regression bugs.

**Complexity**: 3 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] `.github/workflows/ci.yml` runs on every push and PR to main.
2. [x] CI pipeline runs `ruff check`, `mypy .`, and `pytest` using service containers for Qdrant/Redis.
3. [x] Build fails if any check fails.

---

### US-01.04: Initial root documents
**As a** Drishti Contributor  
**I want** standard repository management files (README, Makefile) in the project root  
**So that** I can easily learn how to build, test, and run the project.

**Complexity**: 3 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] `README.md` includes system flow diagrams, quick start guides, and technology listings.
2. [x] `Makefile` maps targets for `setup`, `lint`, `type-check`, `test`, and `run`.

---

### US-01.05: Community documents
**As a** Public Contributor  
**I want** repository rules regarding contributions, licensing, and security  
**So that** I know how to contribute responsibly and securely.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] `CONTRIBUTING.md` details coding standards and branch strategies.
2. [x] `AGENTS.md` provides prompt-based instructions for AI assistants.
3. [x] `CODE_OF_CONDUCT.md` and `SECURITY.md` define standards of conduct and vulnerability reporting.
