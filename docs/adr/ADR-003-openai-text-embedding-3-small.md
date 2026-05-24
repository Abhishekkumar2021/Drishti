# ADR-003: OpenAI text-embedding-3-small

## Status
Approved

## Context & Problem Statement
We need an embedding model to convert code blocks and documentation text into dense vector representations. The model must perform well on code understanding tasks, keep dimensionality manageable to reduce storage costs, and have high throughput.

## Decision
We select **OpenAI's `text-embedding-3-small`** as our primary dense embedding model.

## Alternatives Considered
* **`text-embedding-ada-002`**: Older generation model. It has higher latency and lower benchmark performance compared to `text-embedding-3-small`.
* **Local HuggingFace Models (e.g. `BGE-large` or `instructor-large`)**: Require hosting GPU/CPU infrastructure, increasing operation costs and setup complexity.

## Consequences
* **Pros**:
  * Low cost per token with high rate limits.
  * Excellent benchmark performance on code and text retrieval tasks.
  * Standardized 1536-dimension vectors fit well within Qdrant storage.
* **Cons**:
  * Dependency on external API; requires internet connection and API token setup.
