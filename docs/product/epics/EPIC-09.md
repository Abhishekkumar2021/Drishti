# EPIC-09: Dependency Graph & Impact Analysis

This epic covers setting up the Neo4j graph database to map file, package, class, and method relationships, enabling change impact analysis.

---

## Epic Metadata
* **Complexity**: 34 Story Points
* **Priority**: P2 (Medium Priority)
* **Status**: Planned

---

## User Stories

### US-09.01: Neo4j database setup & schema definition
**As a** Graph Database Administrator  
**I want** a Neo4j graph instance running locally alongside our services  
**So that** we can write relationship models for the codebase.

**Complexity**: 8 SP | **Priority**: P2

**Acceptance Criteria**
1. [ ] Neo4j service runs in docker-compose.
2. [ ] Schema defines node types: `Package`, `File`, `Class`, `Interface`, `Method`.
3. [ ] Schema defines relation types: `CONTAINS`, `EXTENDS`, `IMPLEMENTS`, `CALLS`, `DEPENDS_ON`.

---

### US-09.02: Graph builder
**As a** Graph Architect  
**I want** to parse static code structures and insert them as nodes and relationships in Neo4j  
**So that** the graph represents the current structure of the repository.

**Complexity**: 13 SP | **Priority**: P2

**Acceptance Criteria**
1. [ ] Ingestion pipeline inserts nodes for classes and methods.
2. [ ] Creates `CONTAINS` relationships based on AST hierarchies.
3. [ ] Creates `CALLS` and `DEPENDS_ON` relationships from static import and invocation extraction.

---

### US-09.03: Dependency tracing algorithm
**As a** Security Auditor  
**I want** to query the downstream dependencies of any method or class  
**So that** I can trace the impact of code modifications.

**Complexity**: 8 SP | **Priority**: P2

**Acceptance Criteria**
1. [ ] Implements a Cypher graph query to recursively traverse outgoing relationships.
2. [ ] Identifies all classes and methods that would be affected by modifying a given class/method.

---

### US-09.04: Change impact analysis endpoint
**As a** Tech Lead  
**I want** an API endpoint that takes a file/symbol and returns its dependency impact tree  
**So that** I can review the impact of code changes before merging PRs.

**Complexity**: 5 SP | **Priority**: P2

**Acceptance Criteria**
1. [ ] Endpoint `/api/v1/impact-analysis` accepts file path and line number.
2. [ ] Identifies the defining symbol at that position and runs the tracing query.
3. [ ] Returns a structured JSON dependency tree.
