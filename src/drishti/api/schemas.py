"""Pydantic request and chunk schemas for the Drishti API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UniversalChunk(BaseModel):
    """Universal schema representation for any document or code block.

    Matches the design specification defined in high-level-architecture.md.
    """

    id: str = Field(..., description="Unique UUIDv4 identifier for the chunk")
    source_id: str = Field(..., description="Git commit hash or document file content hash")
    content: str = Field(..., description="Raw text content or code segment")
    content_type: Literal["code", "text", "table", "image_description", "api_endpoint"] = Field(
        ..., description="The semantic classification of content"
    )
    file_path: str = Field(..., description="Relative workspace path of the origin file")
    source_type: Literal["git_repo", "pdf", "markdown", "image", "openapi"] = Field(
        ..., description="The source mechanism that loaded the file"
    )
    language: str | None = Field(None, description="Programming language name if code")
    start_line: int | None = Field(None, description="1-indexed starting line in source file")
    end_line: int | None = Field(
        None,
        description="1-indexed ending line in source file (inclusive)",
    )
    page_number: int | None = Field(None, description="Page index if extracted from a PDF")
    node_type: str | None = Field(
        None,
        description="AST node type if code (e.g., class_declaration)",
    )
    name: str | None = Field(
        None,
        description="Associated symbol name (e.g. function or class name)",
    )
    parent_class: str | None = Field(
        None,
        description="Name of the enclosing class scope if applicable",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Extracted import or calling dependency references",
    )
    last_modified: datetime = Field(..., description="ISO datetime of last modifications")


class IngestionRequest(BaseModel):
    """Payload trigger schema for starting codebase ingestion."""

    repo_path: str = Field(
        ...,
        description="Absolute local directory path of repository to index",
    )
    branch: str | None = Field("main", description="Target Git branch")
    recursive: bool = Field(True, description="Recursively walk subdirectories")
    force_reindex: bool = Field(False, description="Ignore state hash and re-index all files")


class SearchRequest(BaseModel):
    """Payload request schema for hybrid-vector queries."""

    query: str = Field(..., min_length=1, description="Natural language search query")
    filters: dict[str, str] | None = Field(
        None,
        description="Key-value filters (e.g. {'language': 'python', 'file_path': 'src/*'})",
    )
    limit: int = Field(5, ge=1, le=50, description="Max candidates to retrieve")


class AskRequest(BaseModel):
    """Payload request schema for Q&A (RAG) prompts."""

    question: str = Field(..., description="User query for RAG pipeline")
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of prior messages formatted as [{'role': 'user', 'content': '...'}]",
    )
    filters: dict[str, str] | None = Field(None, description="Metadata scope filters")
