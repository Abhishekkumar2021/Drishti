# Module 01: Tree-sitter AST Parsing

Learn how Drishti uses Tree-sitter for multi-language AST parsing to create semantically meaningful code chunks.

## What You'll Learn

1. How Tree-sitter creates Concrete Syntax Trees (CST)
2. S-expression queries for pattern matching
3. Extracting functions, classes, and methods from code
4. Why AST-aware chunking beats naive text splitting

## Files

| File | Description |
|------|-------------|
| `tree_sitter_demo.ipynb` | Interactive notebook with explanations |
| `parse_demo.py` | Standalone script to parse sample code |
| `sample_code/` | Example files in Python, Java, TypeScript, Go |

## Quick Start

```bash
# Run the notebook
uv run jupyter notebook playground/01-tree-sitter/tree_sitter_demo.ipynb

# Or run the script
uv run python playground/01-tree-sitter/parse_demo.py
```

## Key Concepts

### Why Tree-sitter?

- **Incremental parsing**: Only re-parses changed portions
- **Multi-language**: Same API for Python, Java, TypeScript, Go, etc.
- **Production-ready**: Used by GitHub, Neovim, and other major tools
- **Query language**: S-expression queries for pattern matching

### AST vs Text Chunking

```
Naive (500 chars):        AST-Aware:
┌─────────────────┐      ┌─────────────────┐
│ def foo():      │      │ def foo():      │
│   # half of     │      │   x = 1         │
│   x = 1         │      │   return x + 2  │
│   ret...        │      │                 │
├─────────────────┤      └─────────────────┘
│ ...urn x + 2    │      ┌─────────────────┐
│                 │      │ class Bar:      │
│ class Bar:      │      │   def __init__  │
│   def __init    │      │   ...           │
└─────────────────┘      └─────────────────┘
```

The naive approach breaks `foo()` in half, losing context. AST-aware chunking keeps complete semantic units.
