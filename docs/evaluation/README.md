# Drishti Evaluation Directory

This directory contains the documentation and baseline results for Drishti's RAG evaluation suite.

---

## Directory Contents

| Document | Purpose |
|----------|---------|
| [metrics.md](file:///Users/abhishek/Dev/Drishti/docs/evaluation/metrics.md) | Standardized metrics definitions and formulas for evaluation. |
| [baseline.md](file:///Users/abhishek/Dev/Drishti/docs/evaluation/baseline.md) | Baseline comparison results between naive token chunking and AST-aware chunking. |

---

## Purpose of Evaluation

To build a resume-worthy, engineering-grade AI project, we must prove its performance mathematically. We do not simply rely on subjective "it feels like it works" checks. Instead:
1. We run automated evaluations on every pull request to ensure changes do not degrade search results.
2. We compare alternative embedding models and re-ranker thresholds against our established baseline.
3. We publish evaluation reports transparently in the repository.
