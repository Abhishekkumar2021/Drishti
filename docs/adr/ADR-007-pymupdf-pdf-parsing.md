# ADR-007: PyMuPDF for PDF Layout Parsing

## Status
Approved

## Context & Problem Statement
Repositories include unstructured PDF documents (requirements, specs, manuals). We need a parser that reads PDFs while preserving semantic sections, headers, and tables, rather than outputting a single unorganized stream of text.

## Decision
We select **PyMuPDF (fitz)** as our primary PDF parsing library.

## Alternatives Considered
* **PyPDF2**: Simple but fails on complex page layouts, multi-column documents, and does not support structural table boundaries.
* **pdfplumber**: Excellent table parser but suffers from high memory usage and slow parsing speeds on large technical manuals.

## Consequences
* **Pros**:
  * Extremely fast C-backed execution.
  * Extract text blocks with positional data (x, y coordinates, font size), enabling layout-aware section grouping.
  * Native support for image extraction.
* **Cons**:
  * AGPL license constraints on source modification (must be handled as an isolated wrapper utility in Drishti under the MIT scope).
