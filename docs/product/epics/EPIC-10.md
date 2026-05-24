# EPIC-10: Frontend UI

This epic covers building the interactive web application using Next.js 14, complete with chat UI, code Monaco editor rendering, and citation mapping.

---

## Epic Metadata
* **Complexity**: 55 Story Points
* **Priority**: P1 (High Priority)
* **Status**: Planned

---

## User Stories

### US-10.01: Next.js 14 layout & landing page
**As a** Drishti User  
**I want** a modern, visually stunning web landing page  
**So that** I can configure repositories and start searching.

**Complexity**: 8 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Built with Next.js 14 with a responsive dark-themed sidebar.
2. [ ] Contains panels for repository indexing configuration (e.g. entering repository URL or local paths).
3. [ ] Integrates clean state management tracking selected repository.

---

### US-10.02: Chat interface with streaming responses
**As a** Drishti User  
**I want** a chat pane to ask questions and see responses stream in real-time  
**So that** I can quickly read answers as they generate.

**Complexity**: 13 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Implements a clean chat window with user and AI messages.
2. [ ] Integrates SSE/Fetch stream API to display tokens in real-time.
3. [ ] Renders code blocks inside answers with syntax highlighting.

---

### US-10.03: Monaco Editor component for source code rendering
**As a** Drishti User  
**I want** code files to open in a visual code editor directly in my browser  
**So that** I don't have to open my local IDE to read code.

**Complexity**: 13 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Embeds `@monaco-editor/react` in a right-hand detail pane.
2. [ ] Supports syntax highlighting and line numbering for Python, Java, TS, and Go.
3. [ ] Editor is read-only.

---

### US-10.04: Citation mapping
**As a** Software Engineer  
**I want** to click on an answer's file citation to open that file to the exact line inside the Monaco editor  
**So that** I can immediately inspect the referenced source code.

**Complexity**: 13 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Parses citation tags (e.g. `[src/main.py:L10-15]`) in response text and renders them as clickable links.
2. [ ] Clicking a link loads the target file contents via API.
3. [ ] Scrolls Monaco Editor view to highlight lines 10 to 15.

---

### US-10.05: Interactive dependency graph view
**As a** Tech Lead  
**I want** to see an interactive visual graph of code dependencies  
**So that** I can explore relationships between components.

**Complexity**: 8 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Integrates a graph visualization library (like React Flow or D3).
2. [ ] Displays class and method dependencies visually.
3. [ ] Clicking a graph node loads its corresponding code in the Monaco Editor.
