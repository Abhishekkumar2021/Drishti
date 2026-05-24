# Drishti Product Management Index

Welcome to the Product Management directory. This folder contains the definitions, mission, and release planning for the Drishti system.

---

## Directory Contents

| Document | Purpose |
|----------|---------|
| [PRODUCT-VISION.md](file:///Users/abhishek/Dev/Drishti/docs/product/PRODUCT-VISION.md) | High-level business strategy, user personas, differentiators, and target use cases. |
| [EPICS-OVERVIEW.md](file:///Users/abhishek/Dev/Drishti/docs/product/EPICS-OVERVIEW.md) | The master map of all 12 epics, story points, and dependencies. |
| [epics/](file:///Users/abhishek/Dev/Drishti/docs/product/epics/) | Directory containing individual Epic markdown files (`EPIC-01.md` through `EPIC-12.md`). |
| [releases/RELEASE-PLAN.md](file:///Users/abhishek/Dev/Drishti/docs/product/releases/RELEASE-PLAN.md) | Phased rollout roadmap (Alpha, Beta, v1.0 Production release). |

---

## Feature Priority Definitions

To maintain absolute consistency across all product backlogs, epics, and user stories, Drishti uses a single, unified priority scale. No other document may redefine these priorities.

* **P0 — Critical (Blocker)**: Essential for the core system to function. Must be resolved immediately or in the current sprint. Work cannot progress without these items (e.g., repository setup, basic FastAPI structure, database connectivity).
* **P1 — High (Core MVP)**: Required for a usable product experience. Represents the minimal viable product features (e.g., Tree-sitter parsing for code, standard RAG retrieval, simple user interface, basic evaluations).
* **P2 — Medium (Enhancement)**: Adds significant value, performance optimizations, or expanded support but is not blocker-level (e.g., multi-modal PDF/image ingestion, Neo4j dependency graph, query expansion).
* **P3 — Low (Nice-to-have)**: Optional, localized optimizations, or long-term backlog candidates that can be deferred without affecting the user experience.

---

## User Story Format

Every user story in our epics must adhere to the following standard template to ensure clarity and auditability:

```markdown
### US-XX.YY: [User Story Title]

**As a** [Persona]  
**I want** [capability]  
**So that** [value/benefit]  

**Complexity**: [Story Points: 1, 2, 3, 5, 8, 13] | **Priority**: [P0/P1/P2/P3]

**Acceptance Criteria**
1. [ ] Specific, measurable condition 1
2. [ ] Specific, measurable condition 2
3. [ ] Edge case handled or performance requirement met
```

*Note: In Drishti, we exclusively use the term **Acceptance Criteria** instead of "Deliverables" to maintain a standard Agile product management approach.*
