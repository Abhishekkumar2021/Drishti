"""Pydantic request and chunk schemas for the Drishti API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from drishti.exceptions import PathValidationError
from drishti.utils.paths import resolve_repo_path


class ChatMessage(BaseModel):
    """A single message in a RAG conversation history."""

    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


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
    start_line: int | None = Field(
        None,
        ge=1,
        description="1-indexed starting line in source file",
    )
    end_line: int | None = Field(
        None,
        ge=1,
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
    package_name: str | None = Field(
        None,
        description="Java package or namespace path when applicable",
    )
    decorators: list[str] = Field(
        default_factory=list,
        description="Decorator names applied to the symbol (e.g. dataclass, property)",
    )
    exports: list[str] = Field(
        default_factory=list,
        description="Export modifiers for the symbol (e.g. export, default)",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Extracted import or calling dependency references",
    )
    docstring: str | None = Field(
        None,
        description="Docstring or leading comment block attached to the symbol",
    )
    parameters: list[str] = Field(
        default_factory=list,
        description="Formal parameter descriptors for callable symbols",
    )
    return_type: str | None = Field(
        None,
        description="Declared return type for callable symbols when available",
    )
    cyclomatic_complexity: int | None = Field(
        None,
        ge=1,
        description="McCabe cyclomatic complexity for callable symbol bodies",
    )
    parent_module: str | None = Field(
        None,
        description="Enclosing module or package path for the symbol",
    )
    context_path: str | None = Field(
        None,
        description="Fully qualified structural path (file::scope::symbol)",
    )
    imported_symbols: list[str] = Field(
        default_factory=list,
        description="Symbols imported into the file (types, functions, modules)",
    )
    definition_file_path: str | None = Field(
        None,
        description="File path where this symbol is defined (same file for local defs)",
    )
    last_modified: datetime = Field(..., description="ISO datetime of last modifications")

    @model_validator(mode="after")
    def validate_line_range(self) -> UniversalChunk:
        if (
            self.start_line is not None
            and self.end_line is not None
            and self.end_line < self.start_line
        ):
            msg = "end_line must be greater than or equal to start_line"
            raise ValueError(msg)
        return self


class IngestionRequest(BaseModel):
    """Payload trigger schema for starting codebase ingestion."""

    repo_path: str | None = Field(
        None,
        description="Absolute local directory path of repository to index",
    )
    repo_url: str | None = Field(
        None,
        description="GitHub HTTPS or SSH URL to clone before indexing",
    )
    branch: str | None = Field("main", description="Target Git branch")
    recursive: bool = Field(True, description="Recursively walk subdirectories")
    force_reindex: bool = Field(False, description="Ignore state hash and re-index all files")

    @model_validator(mode="after")
    def validate_repo_source(self) -> IngestionRequest:
        has_path = bool(self.repo_path and self.repo_path.strip())
        has_url = bool(self.repo_url and self.repo_url.strip())
        if has_path == has_url:
            msg = "Provide exactly one of repo_path or repo_url"
            raise ValueError(msg)
        return self

    def resolved_repo_path(self, *, allowed_roots: list[Path] | None = None) -> Path:
        """Validate and resolve the repository path (local or cloned GitHub)."""
        if self.repo_url and self.repo_url.strip():
            from drishti.utils.github import clone_or_pull_github_repo

            return clone_or_pull_github_repo(
                self.repo_url.strip(),
                branch=self.branch,
            )
        if not self.repo_path or not self.repo_path.strip():
            msg = "repo_path is required when repo_url is not set"
            raise ValueError(msg)
        try:
            return resolve_repo_path(self.repo_path.strip(), allowed_roots=allowed_roots)
        except PathValidationError as exc:
            raise ValueError(str(exc)) from exc


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

    question: str = Field(..., min_length=1, description="User query for RAG pipeline")
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Prior conversation turns",
    )
    filters: dict[str, str] | None = Field(None, description="Metadata scope filters")
    workspace_id: str | None = Field(
        None,
        description="When set, apply workspace chunk filter and inject workspace memory",
    )

    @field_validator("conversation_history")
    @classmethod
    def validate_history_length(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        if len(value) > 50:
            msg = "conversation_history must not exceed 50 messages"
            raise ValueError(msg)
        return value


class SourceReadRequest(BaseModel):
    """Request body for reading a repository source file (Monaco / citations)."""

    repo_path: str = Field(
        ...,
        min_length=1,
        description="Absolute path to indexed repository root",
    )
    file_path: str = Field(
        ...,
        min_length=1,
        description="Repository-relative file path",
    )

    def resolved_repo_path(self, *, allowed_roots: list[Path] | None = None) -> Path:
        """Validate and resolve the repository root."""
        try:
            return resolve_repo_path(self.repo_path, allowed_roots=allowed_roots)
        except PathValidationError as exc:
            raise ValueError(str(exc)) from exc
