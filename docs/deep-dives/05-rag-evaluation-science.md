# 05. RAG Evaluation Science: RAGAS & Quality Metrics

---

## Table of Contents

1. [Why Building Drishti Is Hard](#1-why-building-drishti-is-hard)
2. [Core Theory: RAG Triad & Evaluator LLMs](#2-core-theory-rag-triad--evaluator-llms)
3. [RAGAS Metrics Mathematical Models](#3-ragas-metrics-mathematical-models)
4. [Synthetic Dataset Generation](#4-synthetic-dataset-generation)
5. [Drishti's Automated Evaluation Runner](#5-drishtis-automated-evaluation-runner)
6. [How Senior Interviewers Test This](#6-how-senior-interviewers-test-this)
7. [Key Takeaways & What's Next](#7-key-takeaways--whats-next)

---

## 1. Why Building Drishti Is Hard

Evaluating RAG systems qualitatively is difficult:
* Asking "Does the chatbot answer correctly?" and checking a few outputs is subjective, failing to detect regressions across different queries.
* Modifying embedding models or chunk sizes can fix one query but break ten others.
* Traditional NLP metrics (like BLEU or ROUGE) measure exact token overlap between answers, which fails on RAG tasks where the same concept can be explained using different vocabulary.

To solve this, Drishti implements a **quantitative evaluation suite** based on **RAGAS**, calculating precision, recall, and faithfulness on a golden Q&A dataset.

---

## 2. Core Theory: RAG Triad & Evaluator LLMs

RAG quality is evaluated using the **RAG Triad**, which breaks down the relationships between the Query, Retrieved Context, and Generated Response:

```
                  ┌───────────────┐
                  │     Query     │
                  └──────┬────────┘
                    ▲         ▲
  Answer Relevancy  │         │  Context Precision
  (Is it helpful?)  │         │  (Is it noisy?)
                    ▼         ▼
  ┌──────────────────┐       ┌──────────────────┐
  │     Response     │ ────▶ │ Retrieved Context│
  └──────────────────┘       └──────────────────┘
                      Faithfulness
                   (Is it grounded?)
```

Rather than using manual scoring, we leverage an **Evaluator LLM** (e.g. GPT-4o) using structured prompts to identify and score these properties.

---

## 3. RAGAS Metrics Mathematical Models

Drishti evaluates retrieval and generation using four key metrics:

### A. Context Precision
Evaluates if retrieved chunks are relevant and placed at the top of the context block.

$$\text{Context Precision@K} = \frac{\sum_{k=1}^{K} P@k \times \text{rel}(k)}{\text{Total Relevant Chunks in Top } K}$$

### B. Context Recall
Evaluates if the retrieval system found all necessary pieces of information.

$$\text{Context Recall} = \frac{|S_{\text{ground\_truth}} \cap S_{\text{retrieved\_context}}|}{|S_{\text{ground\_truth}}|}$$

### C. Faithfulness
Measures if the response is grounded strictly in the retrieved context.
1. The evaluator LLM parses the response into a list of claims: $C = \{c_1, c_2, \dots, c_n\}$.
2. For each claim $c_i$, the model verifies if it is supported by the retrieved context.

$$\text{Faithfulness} = \frac{\text{Number of supported claims}}{|C|}$$

### D. Answer Relevancy
Measures how well the generated response addresses the query.
1. The evaluator LLM generates $N$ hypothetical queries from the generated response.
2. We compute the cosine similarity between the original user query vector ($\mathbf{q}$) and the generated query vectors ($\mathbf{g}_i$).

$$\text{Answer Relevancy} = \frac{1}{N} \sum_{i=1}^{N} \frac{\mathbf{q} \cdot \mathbf{g}_i}{\|\mathbf{q}\| \|\mathbf{g}_i\|}$$

---

## 4. Synthetic Dataset Generation

To run evaluations, we use a curated **Golden Q&A dataset** containing 50 questions, reference files, and ground-truth answers. To expand this, we also generate synthetic question-answer pairs by:
1. Extracting random code chunks from the repository.
2. Prompting an LLM to generate questions and ground-truth answers based on those chunks.

---

## 5. Drishti's Automated Evaluation Runner

Drishti runs automated quality tests on every commit:
1. **Runner Script**: Executed via `Makefile` (runs `pytest` and `benchmarks/eval_retrieval.py`).
2. **Regression Check**: If the RAGAS metrics drop below the target thresholds (precision > 85%, faithfulness > 95%), the build fails.

---

## 6. How Senior Interviewers Test This

**"Why use an LLM to evaluate another LLM? Isn't that prone to bias?"**
> LLM-based evaluation correlates better with human judgment than traditional metrics like BLEU or ROUGE, which only measure keyword overlap. To minimize evaluator bias, we restrict evaluations to closed-book tasks (e.g. verifying if a claim is explicitly supported by a provided text) rather than asking for general quality ratings.

**"What steps can we take to fix low Context Recall scores?"**
> Low Context Recall indicates that the retrieval system is missing relevant chunks. This can be addressed by:
> 1. Increasing the retrieval limit $K$.
> 2. Improving query expansion to capture technical synonyms.
> 3. Tuning the chunk size to capture more context.

---

## 7. Key Takeaways & What's Next

1. **BLEU and ROUGE are inadequate** for evaluating semantic RAG responses.
2. **The RAG Triad evaluates the relationships** between Query, Context, and Response.
3. **Drishti uses RAGAS** to calculate context precision, recall, faithfulness, and relevancy.
4. **Automated evaluations run in CI** to detect performance regressions.

**Next → [Implementation Overview](file:///Users/abhishek/Dev/Drishti/docs/IMPLEMENTATION_STATUS.md):** Review the completion status of epics and user stories.
