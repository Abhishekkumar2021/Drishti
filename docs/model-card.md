# Model Card: Drishti AI Components

This model card details the artificial intelligence models, embeddings, and re-ranking systems incorporated into Drishti.

---

## 1. OpenAI: `text-embedding-3-small`

### Model Description
* **Developer**: OpenAI
* **Model Type**: Dense semantic text embedder
* **Dimensions**: 1,536 (default)
* **Context Window**: 8,191 tokens

### Intended Use
* Used to compute dense vector representations of parsed code blocks (methods, classes) and text paragraphs.
* Enables semantic search across multi-lingual codebases and technical documents.

### Performance & Limits
* Highly effective at capturing conceptual descriptions ("methods to verify tokens") and mapping them to syntax implementation.
* **Limitations**: Poor retrieval of exact, misspelled variable names or short unique hex tokens. (Compensated in Drishti by combining with BM25 sparse vectors).

---

## 2. Anthropic: `claude-3-5-sonnet`

### Model Description
* **Developer**: Anthropic
* **Model Type**: Large Language Model with multi-modal vision capabilities
* **Context Window**: 200,000 tokens
* **Output Limit**: 8,192 tokens

### Intended Use
* **Generation Engine**: Streams natural language answers with source code blocks and citation structures.
* **Query Expander**: Generates technical synonyms and alternative naming conventions for user queries.
* **Visual Parser**: Analyzes architectural diagrams, UI mockups, and flowchart files (`.png`, `.jpg`, `.svg`) to transcribe them into semantic markdown descriptions.

### Hyperparameter Settings
* **Q&A Generation**: `temperature = 0.1` (low temperature to enforce strict adherence to context and prevent hallucinated answers).
* **Query Expansion**: `temperature = 0.5` (moderate temperature to allow vocabulary variety).

### Limitations & Mitigations
* **Hallucination Risk**: LLMs may refer to functions or files that do not exist.
  * *Mitigation*: Prompt boundaries restrict generation to retrieved context only. The backend parses and checks inline citations against the actual files present in the context before returning them.

---

## 3. Cohere: `rerank-v3`

### Model Description
* **Developer**: Cohere
* **Model Type**: Cross-Encoder Re-ranker model (relevance evaluator)
* **Max Chunk Length**: 4,096 tokens

### Intended Use
* Evaluates semantic matching between the user query and candidate chunks returned by the hybrid search stage.
* Re-orders candidate lists to place the most contextually relevant information at the top of the LLM context.

### Performance & Limits
* Outperforms standard dual-encoder cosine similarity by calculating token-level attention across both query and document text simultaneously.
* **Limitations**: Higher latency and API call overhead compared to direct database retrieval.
  * *Mitigation*: Scoped strictly to evaluate the top 50 retrieved candidates from the first stage, rather than the entire collection.
