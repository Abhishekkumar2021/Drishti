"""API response models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    """Health status for a single infrastructure dependency."""

    status: Literal["connected", "disconnected", "disabled", "not_configured"]


class HealthResponse(BaseModel):
    """Readiness health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    services: dict[str, str]
    version: str
    service: str = "drishti"


class LivenessResponse(BaseModel):
    """Liveness probe response."""

    status: Literal["alive"] = "alive"
    version: str
    service: str = "drishti"


class ErrorDetail(BaseModel):
    """Structured API error payload."""

    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Top-level error response envelope."""

    error: ErrorDetail


class SearchResultItem(BaseModel):
    """A single hybrid search hit."""

    chunk_id: str
    file_path: str
    content: str
    score: float
    start_line: int | None = None
    end_line: int | None = None
    language: str | None = None
    name: str | None = None
    node_type: str | None = None


class SearchResponse(BaseModel):
    """Hybrid search response payload."""

    query: str
    results: list[SearchResultItem]


class CitationItem(BaseModel):
    """Structured citation reference."""

    citation_tag: str
    file_path: str
    start_line: int | None = None
    end_line: int | None = None
    valid: bool = True


class AskResponse(BaseModel):
    """Non-streaming RAG answer."""

    question: str
    answer: str
    citations: list[CitationItem]
    sources: list[SearchResultItem]
    cached: bool = False


class IngestResponse(BaseModel):
    """Incremental repository indexing summary."""

    repo_path: str | None = Field(
        None,
        description="Resolved absolute path indexed (use for source/read after GitHub clone)",
    )
    head_commit: str
    base_commit: str | None = None
    added: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)
    chunks_indexed: int = 0
    chunks_removed: int = 0
    files_parsed: int = 0
    total_chunks_in_store: int = 0
    parseable_files: int = 0
    up_to_date: bool = False


class SourceReadResponse(BaseModel):
    """Source file contents for the web Monaco editor."""

    file_path: str
    content: str
    language: str | None = None
    line_count: int = 0


class AffectedNode(BaseModel):
    """A node affected by a code change."""

    id: str
    name: str
    node_type: str
    file_path: str
    start_line: int | None = None
    end_line: int | None = None


class ImpactAnalysisResponse(BaseModel):
    """Response for impact analysis query."""

    target: AffectedNode = Field(description="The node being analyzed")
    affected_count: int = Field(description="Total number of affected nodes")
    affected_nodes: list[AffectedNode] = Field(
        default_factory=list,
        description="Nodes that would be affected by changes",
    )
    dependency_paths: list[list[str]] = Field(
        default_factory=list,
        description="Paths from target to each affected node",
    )
    impact_summary: dict[str, int] = Field(
        default_factory=dict,
        description="Count of affected nodes by type",
    )


class GraphStatsResponse(BaseModel):
    """Graph database statistics."""

    nodes: dict[str, int] = Field(description="Node counts by type")
    total_nodes: int = Field(description="Total number of nodes")
