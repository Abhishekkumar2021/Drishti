# EPIC-12: Demo, Polish & Deployment

This epic covers productionizing the application configurations, building demo seeding scripts, and writing deployment instructions.

---

## Epic Metadata
* **Complexity**: 21 Story Points
* **Priority**: P1 (High Priority)
* **Status**: Planned

---

## User Stories

### US-12.01: Seed script for sample projects
**As a** Drishti Reviewer  
**I want** a pre-configured seed script to clone a sample project, index it, and run a test query  
**So that** I can test-drive the application in under 5 minutes.

**Complexity**: 8 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Script clones a small public repo (e.g. a sample Flask app) into temporary storage.
2. [ ] Invokes Drishti ingestion API.
3. [ ] Prints verification report confirming ingestion and running a sample search.

---

### US-12.02: Docker production optimization
**As a** DevOps Engineer  
**I want** production-grade Docker compose configurations with persistent volumes and health checks  
**So that** we can host Drishti reliably without data loss.

**Complexity**: 8 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Configures persistent volume storage mappings for Qdrant and Redis.
2. [ ] Implements security hardening (non-root execution).

---

### US-12.03: Final release package deployment guidelines
**As a** System Architect  
**I want** a walkthrough document detailing deployment steps  
**So that** users can install Drishti on standard hosting providers.

**Complexity**: 5 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Provides comprehensive installation guides.
2. [ ] Documents all required environment variables and secrets.
