# Module 05: RAG Evaluation Science

Learn how Drishti evaluates RAG quality using RAGAS metrics.

## What You'll Learn

1. Context Precision & Recall metrics
2. Faithfulness (hallucination detection)
3. Answer Relevancy measurement
4. Building golden datasets for evaluation

## Quick Start

```bash
uv run python playground/05-rag-evaluation/evaluation_demo.py
```

## Key Metrics

| Metric | Question Answered | Target |
|--------|-------------------|--------|
| Context Precision | Are top results relevant? | > 85% |
| Context Recall | Did we find all needed info? | > 90% |
| Faithfulness | Is the answer grounded in context? | > 95% |
| Answer Relevancy | Does the answer address the question? | > 90% |

## Why Evaluation Matters

Without metrics, RAG systems fail silently:
- Retrieval returns irrelevant code
- LLM hallucinates function parameters
- Users lose trust in the system

RAGAS provides automated, reproducible quality measurement.
