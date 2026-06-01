"""Graph database module for dependency analysis.

This module provides Neo4j integration for tracking code dependencies
and performing impact analysis on code changes.

Node Types:
    - Package: A package/module (directory or top-level module)
    - File: A source file
    - Class: A class or interface definition
    - Method: A function or method definition

Relationship Types:
    - CONTAINS: Parent contains child (Package->File, Class->Method)
    - EXTENDS: Class extends another class
    - IMPLEMENTS: Class implements an interface
    - CALLS: Method calls another method
    - DEPENDS_ON: File imports/depends on another file
"""

from __future__ import annotations

from drishti.graph.client import GraphClient
from drishti.graph.models import (
    ClassNode,
    DependencyEdge,
    FileNode,
    GraphNode,
    ImpactResult,
    MethodNode,
    PackageNode,
    RelationType,
)

__all__ = [
    "ClassNode",
    "DependencyEdge",
    "FileNode",
    "GraphClient",
    "GraphNode",
    "ImpactResult",
    "MethodNode",
    "PackageNode",
    "RelationType",
]
