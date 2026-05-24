# ADR-006: Claude API for Generation

## Status
Approved

## Context & Problem Statement
We need a generative model to synthesize retrieved codebase chunks, documentation files, and diagrams into a cohesive, markdown-formatted response containing accurate source citations. The model must excel at complex code reasoning and respect structure constraints.

## Decision
We select **Anthropic's Claude 3.5 Sonnet** via the Anthropic API.

## Alternatives Considered
* **OpenAI GPT-4o**: Very strong, but Claude 3.5 Sonnet historically demonstrates superior performance in multi-file code understanding, syntax tracing, and adhering to strict inline citation formatting rules.
* **Local Models (e.g. Llama-3-70B)**: Slow execution speeds on consumer hardware and less reliable in following complex JSON output formats or XML-tagged contexts.

## Consequences
* **Pros**:
  * Industry-leading reasoning performance on coding queries.
  * Native multi-modal image support allows parsing repository diagrams.
  * Large context window (200k tokens) easily handles multi-file references.
* **Cons**:
  * External API cost and dependency.
