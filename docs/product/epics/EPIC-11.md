# EPIC-11: Evaluation & Benchmarking

This epic covers implementing the RAG evaluation framework using RAGAS, Golden Q&A datasets, and benchmark runners.

---

## Epic Metadata
* **Complexity**: 34 Story Points
* **Priority**: P1 (High Priority)
* **Status**: Planned

---

## User Stories

### US-11.01: Golden Q&A dataset curation
**As a** Drishti ML Engineer  
**I want** a curated set of questions, reference code/documents, and ground-truth answers  
**So that** we can evaluate retrieval and generation quality consistently.

**Complexity**: 8 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Dataset contains 50+ questions covering code structure, API specs, and document details.
2. [ ] Each entry has `question`, `expected_files`, `ground_truth_answer`.
3. [ ] Stored in JSON format under `benchmarks/datasets/golden_qa.json`.

---

### US-11.02: RAGAS evaluation runner script
**As a** Drishti CI/CD Automation  
**I want** a script to execute RAGAS metrics on the golden dataset  
**So that** we get score reports on context precision, recall, and faithfulness.

**Complexity**: 13 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Script loads golden dataset, queries `/api/v1/ask` and retrieves results.
2. [ ] Invokes RAGAS library to evaluate Context Precision, Context Recall, and Faithfulness.
3. [ ] Outputs metrics as JSON reports under `benchmarks/results/`.

---

### US-11.03: Comparative dashboard
**As a** Technical Reviewer  
**I want** to see side-by-side metric comparison between AST-aware chunking and naive chunking  
**So that** I can verify the mathematical improvement of AST chunking.

**Complexity**: 13 SP | **Priority**: P1

**Acceptance Criteria**
1. [ ] Runs index generation using naive chunking (500 tokens fixed-size).
2. [ ] Runs evaluation on naive dataset and saves scores.
3. [ ] Generates a console comparison table and markdown chart demonstrating performance differences.
