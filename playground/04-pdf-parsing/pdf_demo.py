#!/usr/bin/env python3
"""PDF Layout Analysis Demo.

This script demonstrates PyMuPDF features used in Drishti:
- Layout-aware text extraction
- Font-based header detection
- Table conversion to markdown

Run with: uv run python playground/04-pdf-parsing/pdf_demo.py

Note: This demo creates a sample PDF in memory for demonstration.
"""

from __future__ import annotations

import io

import fitz  # PyMuPDF


def create_sample_pdf() -> bytes:
    """Create a sample PDF document for demonstration."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size

    # Add a title (large font)
    page.insert_text(
        point=(72, 72),
        text="Authentication System Design",
        fontsize=24,
        fontname="helv",
    )

    # Add a section header (medium font)
    page.insert_text(
        point=(72, 120),
        text="1. Overview",
        fontsize=16,
        fontname="helv",
    )

    # Add body text (normal font)
    body_text = """
The authentication system uses JWT tokens for stateless
authentication. Users authenticate via username/password
or OAuth2 providers (Google, GitHub).
""".strip()
    page.insert_text(
        point=(72, 150),
        text=body_text,
        fontsize=12,
        fontname="helv",
    )

    # Add another section
    page.insert_text(
        point=(72, 250),
        text="2. Token Flow",
        fontsize=16,
        fontname="helv",
    )

    page.insert_text(
        point=(72, 280),
        text="1. Client sends credentials\n2. Server validates and issues JWT\n3. Client includes JWT in headers",
        fontsize=12,
        fontname="helv",
    )

    # Save to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


def extract_text_blocks(page: fitz.Page) -> list[dict]:
    """Extract text blocks with position and font info."""
    blocks = []
    text_dict = page.get_text("dict")

    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:  # Text block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    blocks.append({
                        "text": span.get("text", "").strip(),
                        "font_size": span.get("size", 12),
                        "font_name": span.get("font", ""),
                        "bbox": span.get("bbox", []),
                        "origin": span.get("origin", []),
                    })

    return [b for b in blocks if b["text"]]


def classify_block(block: dict) -> str:
    """Classify a text block based on font size."""
    size = block["font_size"]
    if size >= 20:
        return "title"
    elif size >= 14:
        return "heading"
    else:
        return "body"


def main() -> None:
    """Run the PDF parsing demo."""
    print("=" * 60)
    print("PDF Layout Analysis Demo (PyMuPDF)")
    print("=" * 60)

    # Create sample PDF
    print("\n1. CREATING SAMPLE PDF")
    print("-" * 40)
    pdf_bytes = create_sample_pdf()
    print(f"Created in-memory PDF: {len(pdf_bytes)} bytes")

    # Open the PDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]

    # Raw text extraction
    print("\n2. RAW TEXT EXTRACTION")
    print("-" * 40)
    raw_text = page.get_text()
    print(repr(raw_text[:200]) + "...")
    print("\n⚠️ Notice: No structure, all text concatenated")

    # Layout-aware extraction
    print("\n3. LAYOUT-AWARE EXTRACTION")
    print("-" * 40)
    blocks = extract_text_blocks(page)

    for block in blocks[:10]:
        block_type = classify_block(block)
        print(f"  [{block_type:8}] (size={block['font_size']:4.1f}) {block['text'][:50]}")

    # Structured output
    print("\n4. STRUCTURED OUTPUT")
    print("-" * 40)

    current_heading = None
    for block in blocks:
        block_type = classify_block(block)
        if block_type == "title":
            print(f"\n# {block['text']}")
        elif block_type == "heading":
            current_heading = block["text"]
            print(f"\n## {block['text']}")
        else:
            print(f"  {block['text']}")

    # Image extraction demo
    print("\n5. IMAGE EXTRACTION")
    print("-" * 40)
    images = page.get_images()
    if images:
        print(f"Found {len(images)} images:")
        for img in images:
            print(f"  - xref={img[0]}, size={img[2]}x{img[3]}")
    else:
        print("No images in this demo PDF")
        print("In real PDFs, extracted images go to Claude Vision for description")

    # Table detection hint
    print("\n6. TABLE DETECTION")
    print("-" * 40)
    print("""
Drishti's PDFParser:
1. Uses page.find_tables() to detect table regions
2. Extracts cell contents preserving structure
3. Converts to markdown table format:

   | Column1 | Column2 |
   |---------|---------|
   | Cell1   | Cell2   |

4. Each table becomes a separate chunk with page_number metadata
""")

    # Chunking strategy
    print("\n7. CHUNKING STRATEGY")
    print("-" * 40)
    print("""
Each heading section becomes a chunk:

┌─────────────────────────────────────┐
│ Chunk 1: "Authentication System..." │
│   content_type: "text"              │
│   page_number: 1                    │
│   node_type: "title"                │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Chunk 2: "1. Overview"              │
│   + body text under this heading    │
│   page_number: 1                    │
│   node_type: "section"              │
└─────────────────────────────────────┘
""")

    doc.close()
    print("\n✅ Demo complete")


if __name__ == "__main__":
    main()
