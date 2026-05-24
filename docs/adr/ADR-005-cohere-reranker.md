# ADR-005: Cohere Re-ranking Engine

## Status
Approved

## Context & Problem Statement
Vector databases return chunks based on cosine similarities, which may contain irrelevant noise. To improve LLM answer quality and prevent context window pollution, we need a high-accuracy cross-encoder model to re-score and filter the retrieved candidates.

## Decision
We select **Cohere Rerank API (rerank-v3.5)** as our re-ranking step.

## Alternatives Considered
* **Local Cross-Encoders (e.g. `bge-reranker-large`)**: High GPU/CPU resource requirements make them slow on standard local developer laptops.
* **No Re-ranking**: Results in lower precision and sends irrelevant code blocks to the LLM, leading to hallucinations.

## Consequences
* **Pros**:
  * Cross-encoder evaluates exact question-to-context semantic alignment.
  * Significantly reduces token counts passed to Claude.
* **Cons**:
  * Adds an external API call, introducing ~100-200ms latency to the retrieval step.
