# EPIC-04: Document Ingestion Pipeline

This epic covers parsing unstructured documentation including PDFs, markdown, image-based architecture diagrams, and OpenAPI schemas.

---

## Epic Metadata
* **Complexity**: 42 Story Points
* **Priority**: P1 (High Priority)
* **Status**: Planned

---

## User Stories

### US-04.01: PDF layout-aware parser (PyMuPDF)
**As a** Drishti Ingestion Service  
**I want** to parse PDF manuals and specification files while preserving layouts, headings, and page references  
**So that** text is chunked according to semantic boundaries instead of naive paragraph cuts.

**Complexity**: 8 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] PyMuPDF reads PDF documents.
2. [ ] Detects headings and uses them to establish page hierarchy.
3. [ ] Captures exact page numbers for citations.

---

### US-04.02: PDF table structure extraction
**As a** Business Analyst  
**I want** tables inside PDFs to be extracted as markdown or CSV schemas  
**So that** numerical data is searchable and contextually readable.

**Complexity**: 8 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Detects bounding boxes of tables inside PDFs.
2. [ ] Converts rows and columns into clean markdown string tables.
3. [ ] Embeds tabular data with associated column headers.

---

### US-04.03: Markdown header hierarchy parser
**As a** Tech Writer  
**I want** markdown documents to be chunked recursively based on `#`, `##`, and `###` headers  
**So that** each chunk contains its parent section context.

**Complexity**: 8 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Recursively parses markdown files by headers.
2. [ ] Attaches the parent heading context (e.g. `Section 1.2 > Subsection A`) to the metadata of leaf node text blocks.

---

### US-04.04: Multi-modal image analysis
**As a** System Architect  
**I want** architecture flowcharts and diagrams inside the repository to be annotated via Claude Vision  
**So that** visual relationships are converted to semantic text and indexed.

**Complexity**: 13 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Scans repository images (`.png`, `.jpg`, `.svg`).
2. [ ] Invokes Claude 3.5 Sonnet Vision to generate detailed natural language descriptions and transcribe text (OCR).
3. [ ] Indexes the generated image description under the same schema as text chunks.

---

### US-04.05: OpenAPI spec endpoint parser
**As a** Frontend Developer  
**I want** swagger and OpenAPI specs to be parsed at the API endpoint level  
**So that** I can query endpoints directly using natural language.

**Complexity**: 5 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Parses `.yaml` and `.json` OpenAPI schemas.
2. [ ] Generates separate chunks for each API path + HTTP method (e.g., `POST /users`).
3. [ ] Includes query params, request bodies, and success responses in the chunk content.
