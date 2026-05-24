# RAG Evaluation Metrics Definitions

This document defines the mathematical models and target scores for Drishti's RAG evaluation suite.

---

## 1. Context Precision

Context Precision evaluates if the top-ranked retrieved chunks are the most relevant to the query.

* **Formula**:
  $$\text{Context Precision} = \frac{\sum_{k=1}^{K} P@k \times \text{rel}(k)}{\text{Total Relevant Chunks in Top } K}$$
  Where $P@k$ is the precision at rank $k$, and $\text{rel}(k)$ is 1 if chunk $k$ is relevant, 0 otherwise.
* **Target**: **> 85%**

---

## 2. Context Recall

Context Recall evaluates if the retrieval system found all necessary pieces of information from the codebase.

* **Formula**:
  $$\text{Context Recall} = \frac{\text{Relevant Chunks Retrieved}}{\text{Total Ground-Truth Chunks Needed}}$$
* **Target**: **> 90%**

---

## 3. Faithfulness

Faithfulness measures if the LLM's generated response is strictly supported by the retrieved context. This detects hallucinations.

* **Formula**:
  $$\text{Faithfulness} = \frac{\text{Number of generated statements supported by retrieved context}}{\text{Total number of generated statements in answer}}$$
* **Target**: **> 95%**

---

## 4. Answer Relevancy

Answer Relevancy evaluates if the response directly addresses the query.

* **Formula**:
  $$\text{Answer Relevancy} = \frac{1}{N} \sum_{i=1}^{N} \cos(\mathbf{e}_{\text{query}}, \mathbf{e}_{\text{generated\_query\_i}})$$
  Where the evaluator LLM generates $N$ hypothetical questions from the answer, and their embedding vectors $\mathbf{e}$ are compared against the user's query vector.
* **Target**: **> 90%**
