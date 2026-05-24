# EPIC-03: Code Ingestion Pipeline

This epic covers the repository walking, AST parsing using Tree-sitter, language-specific handler registry, structural syntax tree extraction, metadata enrichment, and incremental indexing using git diffs.

---

## Epic Metadata
* **Complexity**: 55 Story Points
* **Priority**: P0 (Critical Blocker)
* **Status**: In Progress

---

## User Stories

### US-03.01: File walk and programming language detection
**As a** Drishti Ingestion Service  
**I want** to scan a local directory, detect code files, and map them to their correct programming language  
**So that** they can be routed to the appropriate Tree-sitter parser.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] Scans files recursively, ignoring patterns listed in `.gitignore`.
2. [x] Detects language based on extension and magic bytes (e.g. `.py` → Python, `.ts` → TypeScript).
3. [x] Integrates with a language registry interface.

---

### US-03.02: Python Tree-sitter integration
**As a** Python Developer  
**I want** to parse Python code into an abstract syntax tree using Tree-sitter  
**So that** we can extract functions, classes, and method boundaries.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] Py-tree-sitter parses python files.
2. [x] Extracts classes, function/method declarations, and decorators.
3. [x] Captures correct line bounds (start/end) for each extracted symbol.

---

### US-03.03: Java Tree-sitter integration
**As a** Java Developer  
**I want** to parse Java code into an abstract syntax tree using Tree-sitter  
**So that** we can extract packages, classes, interfaces, and methods.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [x] Tree-sitter parses Java files.
2. [x] Extracts packages, interfaces, class definitions, and methods.
3. [x] Preserves class member fields and method signatures.

---

### US-03.04: JavaScript/TypeScript Tree-sitter integration
**As a** frontend developer  
**I want** to parse JS and TS files into abstract syntax trees  
**So that** we can extract react components, hooks, functions, interfaces, and classes.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Tree-sitter parses `.js`, `.jsx`, `.ts`, `.tsx` files.
2. [ ] Extracts interfaces, type aliases, ES6 classes, arrow functions, and react components.
3. [ ] Captures export annotations and modules.

---

### US-03.05: Go Tree-sitter integration
**As a** Go Developer  
**I want** to parse Go files into abstract syntax trees  
**So that** we can extract structs, interfaces, methods, and functions.

**Complexity**: 8 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Tree-sitter parses `.go` files.
2. [ ] Extracts structs, interfaces, functions, receiver methods, and imports.

---

### US-03.06: AST node extraction rule engine
**As a** Compiler Engineer  
**I want** a configurable node type router  
**So that** developers can define which syntax nodes represent "meaningful chunks" for each language.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Parser queries syntax nodes based on a configuration file.
2. [ ] Ignores nodes below a specific line threshold (e.g. functions < 3 lines merged with parent).

---

### US-03.07: Metadata enrichment
**As a** Search Developer  
**I want** to extract docstrings, parameters, return types, and cyclomatic complexity for each chunk  
**So that** search filters can use structural annotations.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Attaches docstrings/comments situated above the AST node.
2. [ ] Calculates basic cyclomatic complexity for methods.
3. [ ] Extracts parameter list and return type annotations.

---

### US-03.08: Parent/child relationship linking
**As a** Knowledge Graph Developer  
**I want** to track the hierarchy of classes, nested classes, and methods  
**So that** we can rebuild context during retrieval.

**Complexity**: 3 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Extracted method chunks include a `parent_class` or `parent_module` identifier in their metadata.
2. [ ] Allows tracing from a child chunk back to its parent context.

---

### US-03.09: Dependency/import extraction
**As a** Dependency Architect  
**I want** to parse import statements in code files  
**So that** we can identify static relationships between chunks.

**Complexity**: 3 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Extracts imported symbols and external packages from files.
2. [ ] Maps code symbols to their defining file path.

---

### US-03.10: Repository git walker
**As a** DevOps Engineer  
**I want** to run incremental indexing based on git diffs  
**So that** we only parse and re-embed files that have changed since the last index run.

**Complexity**: 5 SP | **Priority**: P0

**Acceptance Criteria**
1. [ ] Queries git diff hashes between the workspace and the indexed state.
2. [ ] Detects deleted, modified, and created files.
3. [ ] Removes deleted file chunks from the index database.
