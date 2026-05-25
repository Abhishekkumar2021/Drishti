"""Register document parsers on the shared ingestion registry."""

from __future__ import annotations

from drishti.ingestion.base import ParserRegistry
from drishti.ingestion.documents.markdown import MarkdownParser
from drishti.ingestion.documents.openapi import OpenApiParser
from drishti.ingestion.documents.pdf import PdfParser


def register_document_parsers(registry: ParserRegistry) -> None:
    """Attach EPIC-04 document parsers to an existing registry."""
    markdown = MarkdownParser()
    for extension in (".md", ".mdx"):
        registry.register(extension, markdown)

    registry.register(".pdf", PdfParser())

    openapi = OpenApiParser()
    for extension in (".yaml", ".yml", ".json"):
        registry.register(extension, openapi)
