# ADR-002: Tree-sitter AST Parsing

## Context & Problem Statement
To build an AST-aware RAG system, we need to parse source code files into semantic components (classes, interfaces, methods) rather than chunking them by line counts. The parser must support multiple programming languages (Python, Java, TS, Go) and execute quickly.

## Decision
We select **Tree-sitter** (via its Python bindings) as the syntax parsing engine.

## Alternatives Considered
* **Built-in `ast` module (Python only)**: Restricted to Python; we require a multi-language parser engine.
* **Regex-based chunking**: Highly fragile, breaks when syntax formats vary (e.g., multi-line signatures, decorators), and fails to capture structural hierarchy.
* **ANTLR**: Powerful but requires compiling grammars manually for each language and has higher runtime performance overhead in Python.

## Consequences
* **Pros**:
  * Lightning-fast parsing of source code into syntax trees.
  * Robust, incremental parsing (handling partially invalid code).
  * Standardized S-expression query syntax to extract methods/classes across different languages.
* **Cons**:
  * Requires compiled C/C++ language grammars, increasing build complexity. (Mitigated using modern Python wrappers or pre-compiled bindings).
