# 01. Tree-sitter Internals & AST-Aware Parsing

---

## Table of Contents

1. [Why Building Drishti Is Hard](#1-why-building-drishti-is-hard)
2. [Core Theory: Concrete Syntax Trees (CST) vs. Abstract Syntax Trees (AST)](#2-core-theory-concrete-syntax-trees-cst-vs-abstract-syntax-trees-ast)
3. [Inside Tree-sitter: Incremental Parsing & GLR](#3-inside-tree-sitter-incremental-parsing--glr)
4. [Drishti's AST Extraction Rules](#4-drishtis-ast-extraction-rules)
5. [How Senior Interviewers Test This](#5-how-senior-interviewers-test-this)
6. [Key Takeaways & What's Next](#6-key-takeaways--whats-next)

---

## 1. Why Building Drishti Is Hard

Standard RAG assumes documents consist of unstructured natural language text. However, source code is highly structured, mathematical, and hierarchical:

```
┌──────────────────────────────────────────────┐
│  Raw Character Splitting (Naive)              │
│                                              │
│  line 1: def login(user, password):          │
│  line 2:     hashed = hash(password)         │
│  ─────── [Cut Point: 100 characters] ─────── │
│  line 3:     return db.users.check(hashed)   │
│                                              │
│  Chunk A: lines 1-2 (No return logic!)       │
│  Chunk B: line 3    (No context of who returns!)
└──────────────────────────────────────────────┘
```

When raw partition boundaries split functions:
* The semantic meaning is lost.
* LLMs generate hallucinated guesses because they lack context of imports or parameters.
* Search retrieves incomplete code blocks, leaving developers with broken answers.

To resolve this, Drishti parses code into **Abstract Syntax Trees**, preserving language syntax boundaries and class hierarchy.

---

## 2. Core Theory: Concrete Syntax Trees (CST) vs. Abstract Syntax Trees (AST)

To understand code chunking, we must distinguish between the two types of syntax trees:

### Concrete Syntax Trees (CST)
A CST represents the grammar of a programming language exactly. It contains every detail, including terminal symbols like commas, semicolons, brackets, parentheses, and spaces:
```
                MethodDeclaration
              /   /      \      \
        Return  Name   Params    Body
          |      |     / | \      |
        void   login  (  ... )   {...}
```

### Abstract Syntax Trees (AST)
An AST strips away syntactic details, retaining only the structural execution nodes (the "meaning" of the code). Semicolons and brackets are discarded:
```
              MethodNode [name="login"]
             /          \
      Parameters         MethodBody
    [user, password]      [statements]
```
Drishti works directly with syntax trees to find boundary coordinates for functional blocks (classes, methods).

---

## 3. Inside Tree-sitter: Incremental Parsing & GLR

Drishti uses **Tree-sitter** for syntax parsing because of two technical advantages:

### A. Generalized LR (GLR) Parsing
Traditional compilers use LR parsing, which fails on languages with ambiguous syntax (like C++ or JavaScript). Tree-sitter uses a **Generalized LR (GLR)** parser. When an ambiguous code structure is encountered, the parser splits its execution state and evaluates multiple potential trees in parallel, merging them once the ambiguity is resolved.

### B. Incremental Parsing
When a file is modified, compiling the entire tree is wasteful. Tree-sitter retains the old syntax tree and only parses the modified region, updating affected branches in $O(\log N)$ time. This is critical for Drishti's incremental git-diff indexing.

---

## 4. Drishti's AST Extraction Rules

Drishti translates tree traversals into chunks by routing files to specific language parsers:

1. **Target Identification**: We execute Tree-sitter Queries (written in Lisp-like S-expression syntax) to match class and method nodes.
2. **Coordinate Mapping**: When a query matches, we extract the start and end line coordinates from the matched nodes.
3. **Threshold Filtering**: Chunks below 3 lines (e.g. simple getters/setters) are merged into their enclosing parent class to prevent noise.
4. **Metadata Extraction**: Docstrings immediately preceding the AST node are captured and attached to the chunk payload.

---

## 5. How Senior Interviewers Test This

**"Why choose Tree-sitter over Pythons native `ast` module or standard regex?"**
> Python's `ast` module only parses Python, which violates our multi-language requirement. Regex-based parsing is fragile, failing on multi-line statements, decorators, or nested class definitions. Tree-sitter parses multiple languages using compiled C/C++ grammars, supports incremental parses, and executes quickly.

**"What happens to the AST parser if the repository contains broken code that fails to compile?"**
> Tree-sitter is designed for real-time IDE syntax highlighting, meaning it handles syntax errors gracefully. It builds `ERROR` nodes for broken lines, allowing the parser to extract valid classes and methods from the rest of the file rather than crashing.

---

## 6. Key Takeaways & What's Next

1. **Naive chunking breaks code structures**, leading to hallucinated LLM responses.
2. **CST contains formatting details**, whereas **AST represents structural logic**.
3. **Tree-sitter uses GLR parsing** to support multiple languages and incremental updates.
4. **Drishti filters AST matches** to prevent noise from short functions.

**Next → [02. Embedding Models Compared](02-embedding-models-compared.md):** Compare dense and sparse embeddings, and understand how they are stored in vector databases.
