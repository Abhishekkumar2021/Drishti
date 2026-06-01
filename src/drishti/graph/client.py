"""Neo4j client wrapper for graph database operations.

Provides async-compatible interface to Neo4j for storing and
querying code dependency graphs.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from neo4j import AsyncDriver, AsyncGraphDatabase

from drishti.graph.models import (
    ClassNode,
    DependencyEdge,
    FileNode,
    GraphNode,
    ImpactResult,
    MethodNode,
    PackageNode,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


class GraphClient:
    """Async Neo4j client for dependency graph operations."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "",
    ) -> None:
        """Initialize the Neo4j client.

        Args:
            uri: Neo4j Bolt protocol URI.
            user: Database username.
            password: Database password.
        """
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
            )
            await self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", self._uri)

    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Disconnected from Neo4j")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[Any]:
        """Get an async session for database operations."""
        if self._driver is None:
            await self.connect()
        assert self._driver is not None
        async with self._driver.session() as session:
            yield session

    async def ensure_schema(self) -> None:
        """Create indexes and constraints for optimal query performance."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Package) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Method) REQUIRE m.id IS UNIQUE",
        ]
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.file_path)",
            "CREATE INDEX IF NOT EXISTS FOR (c:Class) ON (c.name)",
            "CREATE INDEX IF NOT EXISTS FOR (m:Method) ON (m.name)",
            "CREATE INDEX IF NOT EXISTS FOR (m:Method) ON (m.parent_class)",
        ]

        async with self.session() as session:
            for query in constraints + indexes:
                await session.run(query)
            logger.info("Graph schema ensured")

    async def clear_graph(self, file_path: str | None = None) -> int:
        """Remove nodes from the graph.

        Args:
            file_path: If provided, only remove nodes for this file.
                       If None, clears the entire graph.

        Returns:
            Number of nodes deleted.
        """
        async with self.session() as session:
            if file_path:
                result = await session.run(
                    """
                    MATCH (n)
                    WHERE n.file_path = $file_path
                    DETACH DELETE n
                    RETURN count(n) as deleted
                    """,
                    file_path=file_path,
                )
            else:
                result = await session.run(
                    """
                    MATCH (n)
                    DETACH DELETE n
                    RETURN count(n) as deleted
                    """
                )
            record = await result.single()
            count = record["deleted"] if record else 0
            logger.info("Deleted %d nodes%s", count, f" for {file_path}" if file_path else "")
            return count

    async def upsert_package(self, node: PackageNode) -> None:
        """Create or update a Package node."""
        async with self.session() as session:
            await session.run(
                """
                MERGE (p:Package {id: $id})
                SET p.name = $name,
                    p.file_path = $file_path,
                    p.package_path = $package_path,
                    p.start_line = $start_line,
                    p.end_line = $end_line
                """,
                **node.model_dump(),
            )

    async def upsert_file(self, node: FileNode) -> None:
        """Create or update a File node."""
        async with self.session() as session:
            await session.run(
                """
                MERGE (f:File {id: $id})
                SET f.name = $name,
                    f.file_path = $file_path,
                    f.language = $language,
                    f.package = $package,
                    f.start_line = $start_line,
                    f.end_line = $end_line
                """,
                **node.model_dump(),
            )

    async def upsert_class(self, node: ClassNode) -> None:
        """Create or update a Class node."""
        async with self.session() as session:
            await session.run(
                """
                MERGE (c:Class {id: $id})
                SET c.name = $name,
                    c.file_path = $file_path,
                    c.is_interface = $is_interface,
                    c.docstring = $docstring,
                    c.decorators = $decorators,
                    c.parent_classes = $parent_classes,
                    c.start_line = $start_line,
                    c.end_line = $end_line
                """,
                **node.model_dump(),
            )

    async def upsert_method(self, node: MethodNode) -> None:
        """Create or update a Method node."""
        async with self.session() as session:
            await session.run(
                """
                MERGE (m:Method {id: $id})
                SET m.name = $name,
                    m.file_path = $file_path,
                    m.parent_class = $parent_class,
                    m.parameters = $parameters,
                    m.return_type = $return_type,
                    m.is_async = $is_async,
                    m.docstring = $docstring,
                    m.complexity = $complexity,
                    m.start_line = $start_line,
                    m.end_line = $end_line
                """,
                **node.model_dump(),
            )

    async def create_relationship(self, edge: DependencyEdge) -> None:
        """Create a relationship between two nodes."""
        rel_type = edge.relation_type.value
        query = f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            MERGE (source)-[r:{rel_type}]->(target)
            SET r.line_number = $line_number,
                r.context = $context
        """
        async with self.session() as session:
            await session.run(
                query,
                source_id=edge.source_id,
                target_id=edge.target_id,
                line_number=edge.line_number,
                context=edge.context,
            )

    async def get_downstream_dependencies(
        self,
        node_id: str,
        max_depth: int = 10,
    ) -> list[dict[str, Any]]:
        """Find all nodes that depend on the given node.

        This traces OUTGOING relationships to find nodes that would be
        affected if the source node changes.

        Args:
            node_id: The node ID to trace from.
            max_depth: Maximum traversal depth.

        Returns:
            List of affected nodes with their paths.
        """
        query = """
            MATCH path = (source {id: $node_id})-[*1..$max_depth]->(affected)
            RETURN affected,
                   [rel in relationships(path) | type(rel)] as rel_types,
                   [n in nodes(path) | n.id] as path_ids,
                   length(path) as depth
            ORDER BY depth
        """
        async with self.session() as session:
            result = await session.run(query, node_id=node_id, max_depth=max_depth)
            records = [record async for record in result]
            return [
                {
                    "node": dict(record["affected"]),
                    "rel_types": record["rel_types"],
                    "path": record["path_ids"],
                    "depth": record["depth"],
                }
                for record in records
            ]

    async def get_upstream_dependencies(
        self,
        node_id: str,
        max_depth: int = 10,
    ) -> list[dict[str, Any]]:
        """Find all nodes that the given node depends on.

        This traces INCOMING relationships to find what the node uses.

        Args:
            node_id: The node ID to trace from.
            max_depth: Maximum traversal depth.

        Returns:
            List of dependency nodes with their paths.
        """
        query = """
            MATCH path = (dependency)-[*1..$max_depth]->(target {id: $node_id})
            RETURN dependency,
                   [rel in relationships(path) | type(rel)] as rel_types,
                   [n in nodes(path) | n.id] as path_ids,
                   length(path) as depth
            ORDER BY depth
        """
        async with self.session() as session:
            result = await session.run(query, node_id=node_id, max_depth=max_depth)
            records = [record async for record in result]
            return [
                {
                    "node": dict(record["dependency"]),
                    "rel_types": record["rel_types"],
                    "path": record["path_ids"],
                    "depth": record["depth"],
                }
                for record in records
            ]

    async def find_node_at_position(
        self,
        file_path: str,
        line_number: int,
    ) -> dict[str, Any] | None:
        """Find the most specific node at a given file position.

        Args:
            file_path: Path to the source file.
            line_number: Line number in the file.

        Returns:
            The most specific node (Method > Class > File) at that position.
        """
        query = """
            MATCH (n)
            WHERE n.file_path = $file_path
              AND n.start_line <= $line_number
              AND n.end_line >= $line_number
            RETURN n, labels(n) as labels
            ORDER BY CASE labels(n)[0]
                WHEN 'Method' THEN 1
                WHEN 'Class' THEN 2
                WHEN 'File' THEN 3
                ELSE 4
            END,
            (n.end_line - n.start_line) ASC
            LIMIT 1
        """
        async with self.session() as session:
            result = await session.run(
                query,
                file_path=file_path,
                line_number=line_number,
            )
            record = await result.single()
            if record:
                return {"node": dict(record["n"]), "labels": record["labels"]}
            return None

    async def impact_analysis(
        self,
        file_path: str,
        line_number: int,
        max_depth: int = 10,
    ) -> ImpactResult | None:
        """Perform impact analysis for a symbol at a given position.

        Args:
            file_path: Path to the source file.
            line_number: Line number in the file.
            max_depth: Maximum dependency traversal depth.

        Returns:
            ImpactResult with affected nodes, or None if no node found.
        """
        node_info = await self.find_node_at_position(file_path, line_number)
        if not node_info:
            return None

        node_data = node_info["node"]
        node_id = node_data.get("id", "")
        labels = node_info["labels"]

        target_node = self._dict_to_node(node_data, labels)

        downstream = await self.get_downstream_dependencies(node_id, max_depth)

        affected_nodes: list[GraphNode] = []
        dependency_paths: list[list[str]] = []
        impact_summary: dict[str, int] = {}

        for dep in downstream:
            dep_labels = dep.get("rel_types", [])
            dep_node = self._dict_to_node(dep["node"], dep_labels)
            affected_nodes.append(dep_node)
            dependency_paths.append(dep["path"])

            node_type = type(dep_node).__name__
            impact_summary[node_type] = impact_summary.get(node_type, 0) + 1

        return ImpactResult(
            target_node=target_node,
            affected_nodes=affected_nodes,
            dependency_paths=dependency_paths,
            impact_summary=impact_summary,
        )

    def _dict_to_node(
        self,
        data: dict[str, Any],
        labels: list[str],
    ) -> GraphNode:
        """Convert a Neo4j node dict to a Pydantic model."""
        if "Package" in labels:
            return PackageNode(
                id=data.get("id", ""),
                name=data.get("name", ""),
                file_path=data.get("file_path", ""),
                package_path=data.get("package_path", ""),
                start_line=data.get("start_line"),
                end_line=data.get("end_line"),
            )
        if "File" in labels:
            return FileNode(
                id=data.get("id", ""),
                name=data.get("name", ""),
                file_path=data.get("file_path", ""),
                language=data.get("language", "unknown"),
                package=data.get("package"),
                start_line=data.get("start_line"),
                end_line=data.get("end_line"),
            )
        if "Class" in labels:
            return ClassNode(
                id=data.get("id", ""),
                name=data.get("name", ""),
                file_path=data.get("file_path", ""),
                is_interface=data.get("is_interface", False),
                docstring=data.get("docstring"),
                decorators=data.get("decorators", []),
                parent_classes=data.get("parent_classes", []),
                start_line=data.get("start_line"),
                end_line=data.get("end_line"),
            )
        if "Method" in labels:
            return MethodNode(
                id=data.get("id", ""),
                name=data.get("name", ""),
                file_path=data.get("file_path", ""),
                parent_class=data.get("parent_class"),
                parameters=data.get("parameters", []),
                return_type=data.get("return_type"),
                is_async=data.get("is_async", False),
                docstring=data.get("docstring"),
                complexity=data.get("complexity"),
                start_line=data.get("start_line"),
                end_line=data.get("end_line"),
            )
        return GraphNode(
            id=data.get("id", ""),
            name=data.get("name", ""),
            file_path=data.get("file_path", ""),
            start_line=data.get("start_line"),
            end_line=data.get("end_line"),
        )

    async def get_stats(self) -> dict[str, int]:
        """Get graph statistics."""
        query = """
            MATCH (n)
            WITH labels(n)[0] as label, count(*) as count
            RETURN label, count
            ORDER BY label
        """
        async with self.session() as session:
            result = await session.run(query)
            stats: dict[str, int] = {}
            async for record in result:
                stats[record["label"]] = record["count"]
            return stats
