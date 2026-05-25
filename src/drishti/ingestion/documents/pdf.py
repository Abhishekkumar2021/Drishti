"""Layout-aware PDF parser using PyMuPDF (US-04.01, US-04.02)."""

from __future__ import annotations

import hashlib
import io
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

import fitz

from drishti.api.schemas import UniversalChunk
from drishti.ingestion.base import BaseParser

_MIN_FONT_SIZE = 8.0
_HEADING_SIZE_RATIO = 1.15


@dataclass(frozen=True)
class _TextBlock:
    page_number: int
    text: str
    font_size: float
    y0: float
    x0: float


class PdfParser(BaseParser):
    """Extracts text blocks and tables from PDFs with page-aware citations."""

    def parse(
        self,
        file_content: bytes,
        file_path: str,
        *,
        last_modified: datetime | None = None,
    ) -> list[UniversalChunk]:
        source_id = hashlib.sha256(file_content).hexdigest()
        indexed_at = last_modified if last_modified is not None else datetime.now(UTC)
        chunks: list[UniversalChunk] = []

        with fitz.open(stream=file_content, filetype="pdf") as document:
            for page_index, page in enumerate(document, start=1):
                chunks.extend(
                    self._chunks_from_tables(
                        page,
                        page_number=page_index,
                        file_path=file_path,
                        source_id=source_id,
                        indexed_at=indexed_at,
                    ),
                )
                chunks.extend(
                    self._chunks_from_text_blocks(
                        page,
                        page_number=page_index,
                        file_path=file_path,
                        source_id=source_id,
                        indexed_at=indexed_at,
                    ),
                )

        return chunks

    def _chunks_from_tables(
        self,
        page: fitz.Page,
        *,
        page_number: int,
        file_path: str,
        source_id: str,
        indexed_at: datetime,
    ) -> list[UniversalChunk]:
        chunks: list[UniversalChunk] = []
        try:
            table_finder = page.find_tables()
        except Exception:
            return chunks

        for table_index, table in enumerate(table_finder.tables, start=1):
            try:
                rows = table.extract()
            except Exception:
                continue
            if not rows:
                continue
            markdown = _rows_to_markdown_table(rows)
            if not markdown.strip():
                continue
            chunks.append(
                _build_chunk(
                    content=markdown,
                    file_path=file_path,
                    source_id=source_id,
                    indexed_at=indexed_at,
                    page_number=page_number,
                    content_type="table",
                    name=f"table_{page_number}_{table_index}",
                    context_path=f"page:{page_number}::table:{table_index}",
                ),
            )
        return chunks

    def _chunks_from_text_blocks(
        self,
        page: fitz.Page,
        *,
        page_number: int,
        file_path: str,
        source_id: str,
        indexed_at: datetime,
    ) -> list[UniversalChunk]:
        blocks = _extract_sorted_blocks(page, page_number=page_number)
        if not blocks:
            return []

        body_font = _median_font_size(blocks)
        sections: list[tuple[str, list[_TextBlock]]] = []
        current_heading = f"Page {page_number}"
        current_blocks: list[_TextBlock] = []

        for block in blocks:
            if block.font_size >= body_font * _HEADING_SIZE_RATIO:
                if current_blocks:
                    sections.append((current_heading, current_blocks))
                current_heading = block.text.split("\n", maxsplit=1)[0].strip() or current_heading
                current_blocks = []
                continue
            current_blocks.append(block)

        if current_blocks:
            sections.append((current_heading, current_blocks))

        chunks: list[UniversalChunk] = []
        for heading, section_blocks in sections:
            text = "\n\n".join(item.text.strip() for item in section_blocks if item.text.strip())
            if not text:
                continue
            chunks.append(
                _build_chunk(
                    content=text,
                    file_path=file_path,
                    source_id=source_id,
                    indexed_at=indexed_at,
                    page_number=page_number,
                    content_type="text",
                    name=heading[:120],
                    context_path=f"page:{page_number}::{heading}",
                ),
            )
        return chunks


def _extract_sorted_blocks(page: fitz.Page, *, page_number: int) -> list[_TextBlock]:
    payload = page.get_text("dict")
    blocks: list[_TextBlock] = []
    for block in payload.get("blocks", []):
        if block.get("type") != 0:
            continue
        lines: list[str] = []
        max_size = _MIN_FONT_SIZE
        y0 = float(block.get("bbox", [0, 0, 0, 0])[1])
        x0 = float(block.get("bbox", [0, 0, 0, 0])[0])
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            line_text = "".join(span.get("text", "") for span in spans).strip()
            if line_text:
                lines.append(line_text)
            for span in spans:
                max_size = max(max_size, float(span.get("size", _MIN_FONT_SIZE)))
        text = "\n".join(lines).strip()
        if text:
            blocks.append(
                _TextBlock(
                    page_number=page_number,
                    text=text,
                    font_size=max_size,
                    y0=y0,
                    x0=x0,
                ),
            )
    return sorted(blocks, key=lambda item: (item.y0, item.x0))


def _median_font_size(blocks: list[_TextBlock]) -> float:
    sizes = sorted(block.font_size for block in blocks)
    if not sizes:
        return 12.0
    mid = len(sizes) // 2
    if len(sizes) % 2:
        return sizes[mid]
    return (sizes[mid - 1] + sizes[mid]) / 2


def _rows_to_markdown_table(rows: list[list[str | None]]) -> str:
    cleaned: list[list[str]] = []
    for row in rows:
        cells = [str(cell or "").strip().replace("\n", " ") for cell in row]
        if any(cells):
            cleaned.append(cells)
    if not cleaned:
        return ""
    width = max(len(row) for row in cleaned)
    normalized = [row + [""] * (width - len(row)) for row in cleaned]
    header = normalized[0]
    divider = ["---"] * width
    body = normalized[1:] if len(normalized) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(divider) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def _build_chunk(
    *,
    content: str,
    file_path: str,
    source_id: str,
    indexed_at: datetime,
    page_number: int,
    content_type: Literal["text", "table"],
    name: str,
    context_path: str,
) -> UniversalChunk:
    return UniversalChunk(
        id=str(uuid.uuid4()),
        source_id=source_id,
        content=content,
        content_type=content_type,
        file_path=file_path,
        source_type="pdf",
        language=None,
        page_number=page_number,
        node_type="pdf_block",
        name=name,
        context_path=context_path,
        last_modified=indexed_at,
    )


def build_minimal_pdf_bytes(*, pages: list[str]) -> bytes:
    """Build a small in-memory PDF for tests (one text block per page)."""
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text, fontsize=12)
    buffer = io.BytesIO()
    document.save(buffer)
    document.close()
    return buffer.getvalue()
