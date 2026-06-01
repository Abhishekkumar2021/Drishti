# Drishti Benchmarks: RAG Evaluation Suite

This directory contains the complete evaluation framework for measuring Drishti's RAG pipeline quality using industry-standard RAGAS metrics.

## Overview

The benchmark suite evaluates four key metrics:

| Metric | Description | Target |
|--------|-------------|--------|
| **Context Precision** | Are the top-ranked retrieved chunks relevant? | > 85% |
| **Context Recall** | Did we retrieve all necessary information? | > 90% |
| **Faithfulness** | Is the answer supported by the retrieved context? | > 95% |
| **Answer Relevancy** | Does the answer directly address the question? | > 90% |

## Directory Structure

```
benchmarks/
├── __init__.py           # Package initialization
├── README.md             # This file
├── models.py             # Pydantic schemas for evaluation data
├── metrics.py            # RAGAS metric computation wrappers
├── runner.py             # Main evaluation orchestrator
├── report.py             # Report generation utilities
├── compare.py            # AST vs Naive comparison runner
├── eval_retrieval.py     # Retrieval-only evaluation script
├── eval_generation.py    # Generation-only evaluation script
├── datasets/
│   └── golden_qa.json    # 55 curated Q&A pairs for evaluation
└── results/              # Evaluation output directory (gitignored)
```

## Quick Start

### Prerequisites

1. Drishti API running locally:
   ```bash
   make docker-up
   make dev
   ```

2. A repository indexed:
   ```bash
   curl -X POST http://localhost:8000/api/v1/ingest \
     -H "Content-Type: application/json" \
     -d '{"repo_path": "/path/to/your/repo"}'
   ```

3. Evaluation dependencies installed:
   ```bash
   uv pip install -e ".[eval]"
   ```

### Running Full Evaluation

```bash
# Run complete evaluation with AST chunking
python -m benchmarks.runner --strategy ast

# Run with limited questions for quick test
python -m benchmarks.runner --strategy ast --max-questions 10

# Filter by category
python -m benchmarks.runner --categories code_structure api search
```

### Running Individual Evaluations

```bash
# Retrieval-only (precision & recall)
python -m benchmarks.eval_retrieval

# Generation-only (faithfulness & relevancy)
python -m benchmarks.eval_generation
```

### Comparing AST vs Naive Chunking

```bash
# First, run AST evaluation
python -m benchmarks.runner --strategy ast

# Then run naive evaluation (requires naive index)
python -m benchmarks.runner --strategy naive

# Generate comparison report
python -m benchmarks.compare \
  --ast-report benchmarks/results/eval_ast_*.json \
  --naive-report benchmarks/results/eval_naive_*.json
```

## Golden Q&A Dataset

The `datasets/golden_qa.json` contains 55 hand-curated Q&A pairs covering:

| Category | Count | Description |
|----------|-------|-------------|
| `code_structure` | 10 | Questions about classes, functions, types |
| `api` | 8 | API endpoints, request/response schemas |
| `search` | 8 | Hybrid search, RRF, reranking |
| `ingestion` | 12 | Parsers, AST extraction, incremental indexing |
| `embedding` | 4 | Dense/sparse embeddings, providers |
| `storage` | 4 | Qdrant, filters, chunk indexing |
| `generation` | 6 | RAG pipeline, streaming, citations |
| `agent` | 5 | LangGraph, tools, checkpointer |
| `platform` | 4 | PostgreSQL, MinIO, workers |
| `observability` | 2 | Logging, request tracing |
| `config` | 2 | Settings, environment variables |
| `frontend` | 3 | Next.js, Monaco, streaming |
| `cicd` | 2 | GitHub Actions, Makefile |
| `testing` | 1 | Test organization, markers |
| `database` | 2 | Models, migrations |

Each entry includes:
- `id`: Unique identifier
- `category`: Question category
- `difficulty`: easy/medium/hard
- `question`: The evaluation question
- `expected_files`: Files that should be retrieved
- `expected_chunks`: Specific symbols expected
- `ground_truth_answer`: Correct answer for faithfulness evaluation

## Output Reports

### JSON Reports

Full evaluation data saved to `benchmarks/results/`:
```json
{
  "run_id": "uuid",
  "timestamp": "2024-...",
  "chunking_strategy": "ast",
  "aggregate_metrics": {
    "context_precision_mean": 0.88,
    "context_recall_mean": 0.92,
    "faithfulness_mean": 0.96,
    "answer_relevancy_mean": 0.91
  },
  "individual_results": [...],
  "passed_thresholds": true
}
```

### Console Output

```
╔════════════════════════════════════════════════════════════╗
║  Drishti RAG Evaluation Report                             ║
║  Strategy: ast        Questions: 55                        ║
╠════════════════════════════════════════════════════════════╣
║  Metric               │  Score   │  Target  │  Status      ║
╠═══════════════════════╪══════════╪══════════╪══════════════╣
║  Context Precision    │   88.2%  │   85.0%  │  ✓ PASS      ║
║  Context Recall       │   92.4%  │   90.0%  │  ✓ PASS      ║
║  Faithfulness         │   96.8%  │   95.0%  │  ✓ PASS      ║
║  Answer Relevancy     │   91.5%  │   90.0%  │  ✓ PASS      ║
╠═══════════════════════╧══════════╧══════════╧══════════════╣
║  ✅ ALL THRESHOLDS PASSED                                  ║
╚════════════════════════════════════════════════════════════╝
```

### Markdown Reports

Generated reports include:
- Summary metrics table
- Breakdown by category
- Breakdown by difficulty
- Mermaid visualization charts

## CI Integration

Add to your GitHub Actions workflow:

```yaml
- name: Run RAG Evaluation
  run: |
    python -m benchmarks.runner --max-questions 20
    # Fail if thresholds not met
    python -c "
    import json
    with open('benchmarks/results/eval_ast_*.json') as f:
        report = json.load(f)
    assert report['passed_thresholds'], 'Evaluation thresholds not met'
    "
```

## Extending the Dataset

To add new Q&A pairs:

1. Edit `datasets/golden_qa.json`
2. Follow the schema:
   ```json
   {
     "id": "qa_NNN",
     "category": "category_name",
     "difficulty": "easy|medium|hard",
     "question": "Your question here?",
     "expected_files": ["src/path/to/file.py"],
     "expected_chunks": ["ClassName", "function_name"],
     "ground_truth_answer": "The complete expected answer..."
   }
   ```
3. Run evaluation to verify

## Metrics Deep Dive

See [docs/evaluation/metrics.md](../docs/evaluation/metrics.md) for mathematical definitions.

See [docs/deep-dives/05-rag-evaluation-science.md](../docs/deep-dives/05-rag-evaluation-science.md) for theoretical background.
