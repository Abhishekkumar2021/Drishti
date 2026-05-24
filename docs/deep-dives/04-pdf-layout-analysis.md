# 04. PDF Layout Analysis & Prose Parsing

---

## Table of Contents

1. [Why Building Drishti Is Hard](#1-why-building-drishti-is-hard)
2. [Core Theory: Document Layout Analysis (DLA)](#2-core-theory-document-layout-analysis-dla)
3. [PDF Structural Parsing via PyMuPDF](#3-pdf-structural-parsing-via-pymupdf)
4. [Multi-Modal Visual Parsing](#4-multi-modal-visual-parsing)
5. [Drishti's PDF Parsing Strategy](#5-drishtis-pdf-parsing-strategy)
6. [How Senior Interviewers Test This](#6-how-senior-interviewers-test-this)
7. [Key Takeaways & What's Next](#7-key-takeaways--whats-next)

---

## 1. Why Building Drishti Is Hard

Technical documentation is often stored in PDFs. However, the PDF format was designed for printing, not structured data extraction:

```
PDF VISUAL LAYOUT               PDF RAW BYTE STREAM
┌───────────────────────────┐   ┌───────────────────────────┐
│ Column A      Column B    │   │ Page 1: Column A text     │
│ Paragraph 1   Paragraph 3 │   │ starts here. Column B     │
│ Paragraph 2   Paragraph 4 │   │ text starts next...       │
└───────────────────────────┘   └───────────────────────────┘
```

A naive parser reads characters sequentially as they appear in the raw byte stream. If a PDF has a two-column layout, the parser merges the columns, reading line 1 of Column A followed immediately by line 1 of Column B. This renders the text unreadable and ruins vector embeddings.

To solve this, Drishti implements a **layout-aware parsing** engine that groups text blocks based on font sizes and page coordinate boxes.

---

## 2. Core Theory: Document Layout Analysis (DLA)

Document Layout Analysis (DLA) is the process of identifying and categorizing the physical and logical regions of a document page.

### A. Physical Layout Analysis
Identifies the bounding boxes of paragraphs, headers, tables, images, and columns.

### B. Logical Layout Analysis
Determines the reading order and semantic roles of the blocks (e.g. mapping header blocks to parent sections, and body blocks to children).

---

## 3. PDF Structural Parsing via PyMuPDF

Drishti uses PyMuPDF (fitz) because it exposes positional coordinates for text blocks:

```python
# PyMuPDF block extraction returns:
# (x0, y0, x1, y1, "text block content", block_no, block_type)
```

By sorting blocks vertically ($y_0$) and horizontally ($x_0$), the parser groups column text and handles multi-column layouts correctly. Font sizes are also analyzed to identify headings and structure document sections.

---

## 4. Multi-Modal Visual Parsing

Architecture diagrams (UML, flowcharts, schemas) cannot be read via standard text extraction.
1. When an image block is detected in the PDF, its bounding box is cropped and saved.
2. The image is passed to a vision model (Claude 3.5 Sonnet Vision).
3. The model generates a structured markdown description and transcribes text (OCR).
4. This generated text description is indexed as a chunk in Qdrant, making the diagram searchable via natural language.

---

## 5. Drishti's PDF Parsing Strategy

1. **Extraction**: PyMuPDF parses pages, returning text blocks, tables, and images.
2. **Layout Sorting**: Sorts blocks horizontally to separate column text.
3. **Sectioning**: Analyzes font sizes to split text into sections based on headings.
4. **Table Formatting**: Converts table structures into markdown string tables.
5. **Image Ingestion**: Translates image blocks into text descriptions using Claude Vision.

---

## 6. How Senior Interviewers Test This

**"How does your PDF parser handle tables? Why not treat them as standard text?"**
> Treating tables as standard text strips away cell boundaries, merging rows and columns into single sentences. This destroys the relationships between data points. Drishti extracts tables as structural markdown tables, preserving column and row structures for vector indexing.

**"Why use layout-aware parsing instead of a simpler OCR model for the entire page?"**
> Running OCR models (like Tesseract) on entire pages is slow, expensive, and struggles to preserve multi-column reading order. PyMuPDF extracts text directly from the PDF's native character metadata, which is faster and more accurate. We limit OCR and vision models to image and diagram blocks where native text is unavailable.

---

## 7. Key Takeaways & What's Next

1. **PDFs lack native reading layouts**, meaning simple text extractions can merge columns.
2. **Drishti uses PyMuPDF** to extract text blocks with page coordinates.
3. **Tables are converted to markdown** to preserve cell structures.
4. **Diagrams are described via Claude Vision** and indexed as text chunks.

**Next → [05. RAG Evaluation Science](05-rag-evaluation-science.md):** Learn how RAGAS metrics mathematically evaluate retrieval and generation quality.
