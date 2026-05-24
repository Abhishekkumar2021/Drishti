# Drishti Benchmarks: Retrieval & Generation Performance

This directory will hold scripts and datasets for RAG quality evaluation (**EPIC-11**).

## Current status

Benchmark automation is **not implemented yet**. The golden dataset exists:

| Path | Description |
|------|-------------|
| `datasets/golden_qa.json` | Hand-curated Q&A pairs for future RAGAS evaluation |

Planned scripts (EPIC-11):

- `eval_chunking.py` — AST-aware vs naive chunking comparison
- `eval_retrieval.py` — context precision/recall via RAGAS
- `eval_generation.py` — faithfulness and answer relevancy

## Running benchmarks (when available)

```bash
make benchmark
```

Until EPIC-11 lands, use unit tests and the evaluation docs in `docs/evaluation/`.
