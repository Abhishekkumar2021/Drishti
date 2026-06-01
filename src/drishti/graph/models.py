"""Graph database models for dependency tracking.

Defines Pydantic models for Neo4j nodes and relationships used
in Drishti's dependency graph analysis.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class RelationType(StrEnum):
    """Types of relationships in the dependency graph."""

    CONTAINS = "CONTAINS"
    EXTENDS = "EXTENDS"
    IMPLEMENTS = "IMPLEMENTS"
    CALLS = "CALLS"
    DEPENDS_ON = "DEPENDS_ON"


class GraphNode(BaseModel):
    """Base model for all graph nodes."""

    id: str = Field(description="Unique identifier (typically file_path:name)")
    name: str = Field(description="Short name of the node")
    file_path: str = Field(description="Source file path")
    start_line: int | None = Field(default=None, description="Start line in source")
    end_line: int | None = Field(default=None, description="End line in source")


class PackageNode(GraphNode):
    """A package or module (directory or top-level module)."""

    node_type: Literal["Package"] = "Package"
    package_path: str = Field(description="Full package path (e.g., 'drishti.search')")


class FileNode(GraphNode):
    """A source file node."""

    node_type: Literal["File"] = "File"
    language: str = Field(description="Programming language")
    package: str | None = Field(default=None, description="Parent package name")


class ClassNode(GraphNode):
    """A class or interface definition."""

    node_type: Literal["Class"] = "Class"
    is_interface: bool = Field(default=False, description="True if interface")
    docstring: str | None = Field(default=None, description="Class docstring")
    decorators: list[str] = Field(default_factory=list, description="Class decorators")
    parent_classes: list[str] = Field(default_factory=list, description="Base classes")


class MethodNode(GraphNode):
    """A function or method definition."""

    node_type: Literal["Method"] = "Method"
    parent_class: str | None = Field(default=None, description="Parent class name")
    parameters: list[str] = Field(default_factory=list, description="Parameter list")
    return_type: str | None = Field(default=None, description="Return type annotation")
    is_async: bool = Field(default=False, description="True if async function")
    docstring: str | None = Field(default=None, description="Method docstring")
    complexity: int | None = Field(default=None, description="Cyclomatic complexity")


class DependencyEdge(BaseModel):
    """An edge representing a dependency relationship."""

    source_id: str = Field(description="Source node ID")
    target_id: str = Field(description="Target node ID")
    relation_type: RelationType = Field(description="Type of relationship")
    line_number: int | None = Field(default=None, description="Line where dependency occurs")
    context: str | None = Field(default=None, description="Additional context")


class ImpactResult(BaseModel):
    """Result of an impact analysis query."""

    target_node: GraphNode = Field(description="The node being analyzed")
    affected_nodes: list[GraphNode] = Field(
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

    @property
    def total_affected(self) -> int:
        """Total number of affected nodes."""
        return len(self.affected_nodes)
