"""Unit tests for the graph module (EPIC-09)."""

from __future__ import annotations

import pytest

from drishti.graph.models import (
    ClassNode,
    DependencyEdge,
    FileNode,
    ImpactResult,
    MethodNode,
    PackageNode,
    RelationType,
)


class TestGraphModels:
    """Test graph model validation and serialization."""

    def test_package_node_creation(self) -> None:
        """PackageNode should accept valid package data."""
        node = PackageNode(
            id="src/drishti",
            name="drishti",
            file_path="src/drishti",
            package_path="drishti",
        )
        assert node.node_type == "Package"
        assert node.id == "src/drishti"

    def test_file_node_creation(self) -> None:
        """FileNode should accept valid file data."""
        node = FileNode(
            id="src/drishti/main.py",
            name="main.py",
            file_path="src/drishti/main.py",
            language="python",
            start_line=1,
            end_line=100,
        )
        assert node.node_type == "File"
        assert node.language == "python"

    def test_class_node_creation(self) -> None:
        """ClassNode should accept valid class data."""
        node = ClassNode(
            id="src/drishti/search.py:HybridSearchPipeline",
            name="HybridSearchPipeline",
            file_path="src/drishti/search.py",
            is_interface=False,
            docstring="A hybrid search pipeline combining dense and sparse retrieval.",
            parent_classes=["BaseSearchPipeline"],
            decorators=["dataclass"],
            start_line=10,
            end_line=150,
        )
        assert node.node_type == "Class"
        assert not node.is_interface
        assert "BaseSearchPipeline" in node.parent_classes

    def test_method_node_creation(self) -> None:
        """MethodNode should accept valid method data."""
        node = MethodNode(
            id="src/drishti/search.py:HybridSearchPipeline.search",
            name="search",
            file_path="src/drishti/search.py",
            parent_class="HybridSearchPipeline",
            parameters=["query", "top_k", "filters"],
            return_type="list[SearchResult]",
            is_async=True,
            docstring="Perform hybrid search with RRF fusion.",
            complexity=5,
            start_line=50,
            end_line=80,
        )
        assert node.node_type == "Method"
        assert node.is_async
        assert node.parent_class == "HybridSearchPipeline"

    def test_dependency_edge_creation(self) -> None:
        """DependencyEdge should accept valid edge data."""
        edge = DependencyEdge(
            source_id="src/drishti/main.py",
            target_id="src/drishti/search.py",
            relation_type=RelationType.DEPENDS_ON,
            line_number=5,
            context="from drishti.search import HybridSearchPipeline",
        )
        assert edge.relation_type == RelationType.DEPENDS_ON
        assert edge.line_number == 5

    def test_impact_result_total_affected(self) -> None:
        """ImpactResult.total_affected should count affected nodes."""
        target = FileNode(
            id="src/main.py",
            name="main.py",
            file_path="src/main.py",
            language="python",
        )
        affected = [
            MethodNode(
                id="src/api.py:handler",
                name="handler",
                file_path="src/api.py",
            ),
            ClassNode(
                id="src/service.py:Service",
                name="Service",
                file_path="src/service.py",
            ),
        ]
        result = ImpactResult(
            target_node=target,
            affected_nodes=affected,
            dependency_paths=[["src/main.py", "src/api.py:handler"]],
            impact_summary={"MethodNode": 1, "ClassNode": 1},
        )
        assert result.total_affected == 2


class TestRelationType:
    """Test RelationType enumeration."""

    def test_relation_types_exist(self) -> None:
        """All required relationship types should be defined."""
        assert RelationType.CONTAINS.value == "CONTAINS"
        assert RelationType.EXTENDS.value == "EXTENDS"
        assert RelationType.IMPLEMENTS.value == "IMPLEMENTS"
        assert RelationType.CALLS.value == "CALLS"
        assert RelationType.DEPENDS_ON.value == "DEPENDS_ON"
