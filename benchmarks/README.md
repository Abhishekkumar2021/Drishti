# Drishti Benchmarks: Retrieval & Generation Performance

This directory contains scripts and datasets used to run performance and quality benchmarks against Drishti's search and generation pipelines.

---

## Directory Structure

* **`datasets/golden_qa.json`**: Hand-curated golden dataset containing 50 questions, target files, and ground-truth answers used for quality evaluations.
* **`results/`**: Execution reports, including metrics calculated on baseline runs.
* **`eval_chunking.py`**: Compares AST-aware chunking against naive character splitting.
* **`eval_retrieval.py`**: Computes Context Precision and Context Recall scores using RAGAS.
* **`eval_generation.py`**: Computes Faithfulness and Answer Relevancy scores.

---

## Running Benchmarks

Ensure your environment variables are configured in `.env` (including `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`) and local databases are running via Docker:

### 1. Run the Entire Benchmark Suite
You can run all quality evaluations using the Makefile target:
```bash
make benchmark
```
This runs `scripts/benchmark.sh` under the hood.

### 2. Compare Chunking Strategies Side-by-Side
To run a comparative evaluation of AST-aware chunking vs naive split chunking:
```bash
uv run benchmarks/eval_chunking.py --repo ./src/drishti
```
This output is saved to `benchmarks/results/comparison.json`.

---

## Metric Quality Standards (Targets)

We enforce the following quality thresholds in our CI test runs:
* **Context Precision**: **> 85%**
* **Context Recall**: **> 90%**
* **Faithfulness**: **> 95%**
* **Answer Relevancy**: **> 90%**
