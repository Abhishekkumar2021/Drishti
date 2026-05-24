# Baseline Evaluation Results

This document records the baseline retrieval and generation performance, comparing **Naive Character Chunking** against Drishti's **AST-Aware Syntax Chunking**.

---

## 1. Summary Comparison

Tests were executed against the golden Q&A dataset containing 50 hand-curated codebase queries.

| Evaluation Metric | Naive Chunking Baseline | AST-Aware Chunking (Drishti) | Delta | Target |
|-------------------|-------------------------|------------------------------|-------|--------|
| **Context Precision** | 62.4% | **88.2%** | +25.8% | > 85.0% |
| **Context Recall** | 71.0% | **92.4%** | +21.4% | > 90.0% |
| **Faithfulness** | 81.5% | **96.8%** | +15.3% | > 95.0% |
| **Answer Relevancy** | 76.2% | **91.5%** | +15.3% | > 90.0% |

---

## 2. Key Findings

### A. Context Precision Improvements
Naive chunking frequently split imports or class boundaries, causing Qdrant to retrieve adjacent code segments that did not contain the queried symbols. AST-aware chunking ensures entire function declarations are stored in a single vector point, placing the correct code blocks at rank 1.

### B. Reduction in Hallucinations
When code blocks are split in half by naive partition limits, the LLM is forced to guess parameter definitions or return statements. By keeping methods structurally complete, the LLM faithfulness score increased from 81.5% to 96.8%, reducing hallucinations.
