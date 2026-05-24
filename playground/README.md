# Drishti Playground: Interactive Learning Modules

This directory contains standalone, interactive scripts and Jupyter notebooks designed for testing and learning the core technologies in Drishti.

---

## Playground Modules

| Module Directory | Topic | Description | Key Tech Demoed |
|------------------|-------|-------------|-----------------|
| [01-tree-sitter/](file:///Users/abhishek/Dev/Drishti/playground/01-tree-sitter/) | AST Code Parsing | Parses Python, TS, Java, and Go files into Abstract Syntax Trees. | `tree_sitter`, `python-bindings` |
| [02-qdrant/](file:///Users/abhishek/Dev/Drishti/playground/02-qdrant/) | Vector DB Operations | Performs CRUD operations, payload filtering, and named vector setups in Qdrant. | `qdrant-client` |
| [03-hybrid-search/](file:///Users/abhishek/Dev/Drishti/playground/03-hybrid-search/) | Search Fusion | Combines sparse (BM25) and dense search results using Reciprocal Rank Fusion (RRF). | `numpy`, custom RRF logic |
| [04-pdf-parsing/](file:///Users/abhishek/Dev/Drishti/playground/04-pdf-parsing/) | Layout PDF Parsing | Extracts text blocks, columns, tables, and images from PDFs. | `PyMuPDF (fitz)` |
| [05-rag-evaluation/](file:///Users/abhishek/Dev/Drishti/playground/05-rag-evaluation/) | Automated Evaluation | Computes precision, recall, and faithfulness scores. | `ragas`, `datasets` |

---

## How to Run the Playground Modules

1. **Set Up the Environment**:
   Ensure you have run the setup Makefile command in the root folder:
   ```bash
   make setup
   ```
2. **Launch a Jupyter Server**:
   You can run Jupyter notebooks to explore each playground interactively:
   ```bash
   uv run jupyter notebook
   ```
3. **Execute Python scripts directly**:
   Each module folder contains standalone Python scripts that can be run directly:
   ```bash
   uv run playground/01-tree-sitter/parse_demo.py
   ```
