# LLD Chapter 05: Evaluation Framework

This chapter details the design of Drishti's RAG evaluation suite, focusing on RAGAS metrics, dataset structures, and regression testing runners.

---

## Table of Contents

1. [RAG Evaluation Metrics (RAGAS)](#1-rag-evaluation-metrics-ragas)
2. [Golden Q&A Dataset Schema](#2-golden-qa-dataset-schema)
3. [Evaluation Runner Architecture](#3-evaluation-runner-architecture)
4. [Baseline Comparison (AST vs. Naive)](#4-baseline-comparison-ast-vs-naive)
5. [Code Implementation Blueprint](#5-code-implementation-blueprint)

---

## 1. RAG Evaluation Metrics (RAGAS)

Retrieval-Augmented Generation systems require quantitative quality testing. Drishti implements the RAGAS (Retrieval Augmented Generation Assessment) evaluation framework, which calculates four core scores using an LLM evaluator:

### A. Context Precision
Measures whether all ground-truth relevant chunks retrieved are ranked at the top of the context block. High context precision indicates low noise in the retrieved context.

### B. Context Recall
Measures whether the retrieved context contains all the necessary information to construct the ground-truth answer. High context recall indicates that the system is retrieving everything it should.

### C. Faithfulness
Measures whether the generated LLM response is grounded strictly in the retrieved context, without hallucinated outside details. High faithfulness indicates that the answer is factually correct relative to the source context.

### D. Answer Relevancy
Measures how well the generated answer addresses the user's specific query. Low answer relevancy indicates that the model is outputting redundant, rambling, or off-topic responses.

---

## 2. Golden Q&A Dataset Schema

Evaluation is run against a static, curated list of questions located at `benchmarks/datasets/golden_qa.json`.

```json
[
  {
    "id": "qa_001",
    "question": "What parameters does verify_access_token accept in token.py, and what exceptions does it raise?",
    "expected_files": ["src/auth/token.py"],
    "ground_truth_answer": "The verify_access_token function in src/auth/token.py accepts a single string parameter 'token'. It raises a CredentialsException if the token signature is invalid, expired, or cannot be decoded."
  }
]
```

---

## 3. Evaluation Runner Architecture

The evaluation runner operates as a CLI tool or a scheduled CI workflow (`.github/workflows/evaluate.yml`).

```
  Golden QA Dataset
          │
          ▼
┌──────────────────┐
│  Query Pipeline  │ ──▶ Hits `/api/v1/ask`
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  RAGAS Evaluator │ ──▶ Computes Precision, Recall, Faithfulness
└────────┬─────────┘
         │
         ▼
  JSON Metric Report
```

Reports are saved to `benchmarks/results/` with a timestamp and compared against past runs. If scores drop below a set threshold, the runner exit code is non-zero to fail the build.

---

## 4. Baseline Comparison (AST vs. Naive)

The framework includes a script to index the same code directory using two strategies:
1. **Naive Strategy**: Raw character split (500 tokens, 50 token overlap).
2. **AST-Aware Strategy (Drishti)**: Method and Class boundary parsing.

The golden dataset is executed against both indexing configurations, yielding side-by-side metric tables to verify the improvements of Drishti's parsing rules.

---

## 5. Code Implementation Blueprint

The following blueprint defines the structure of the RAGAS evaluation runner:

```python
import json
from typing import List, Dict, Any
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

class EvaluationSuiteRunner:
    """
    Runner for calculating RAGAS metrics on Drishti endpoints.
    """
    def __init__(self, golden_dataset_path: str, ask_api_url: str):
        self.dataset_path = golden_dataset_path
        self.api_url = ask_api_url
        
    def _load_golden_dataset(self) -> List[Dict[str, Any]]:
        with open(self.dataset_path, "r") as f:
            return json.load(f)
            
    def run_eval(self) -> Dict[str, Any]:
        """
        Executes pipeline queries and invokes RAGAS.
        """
        golden = self._load_golden_dataset()
        
        queries = []
        answers = []
        contexts = []
        ground_truths = []
        
        for item in golden:
            question = item["question"]
            ground_truth = item["ground_truth_answer"]
            
            # Hit `/ask` API to retrieve streaming answer and context
            response = self._hit_ask_endpoint(question)
            
            queries.append(question)
            answers.append(response["answer"])
            contexts.append(response["retrieved_contexts"])  # list of chunk texts
            ground_truths.append(ground_truth)
            
        # Convert lists to HuggingFace dataset format
        data = {
            "question": queries,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
        }
        dataset = Dataset.from_dict(data)
        
        # Invoke RAGAS evaluate
        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall
            ]
        )
        
        return result.to_pandas().to_dict(orient="records")

    def _hit_ask_endpoint(self, question: str) -> Dict[str, Any]:
        # Mocking or executing actual HTTP request to FastAPI Gateway
        # Returns parsed answer and retrieved chunks
        return {
            "answer": "This is a generated answer.",
            "retrieved_contexts": ["chunk 1 content", "chunk 2 content"]
        }
```
