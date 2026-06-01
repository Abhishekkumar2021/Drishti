# Module 04: PDF Layout Analysis

Learn how Drishti extracts structured content from PDF documents using PyMuPDF.

## What You'll Learn

1. Layout-aware text extraction (vs raw text dump)
2. Table detection and conversion to markdown
3. Image extraction for vision analysis
4. Font-based header detection

## Quick Start

```bash
uv run python playground/04-pdf-parsing/pdf_demo.py
```

## Key Concepts

### Why Layout Matters

Raw text extraction loses structure:
```
# Raw extraction:
"Header1Header2Row1Col1Row1Col2Row2Col1Row2Col2"

# Layout-aware extraction:
| Header1 | Header2 |
|---------|---------|
| Row1Col1| Row1Col2|
```

### PyMuPDF Features

- **Text blocks**: Positioned text with coordinates
- **Font analysis**: Size, weight for header detection
- **Tables**: Convert to markdown format
- **Images**: Extract for vision model analysis
