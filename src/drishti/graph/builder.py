"""Graph builder for extracting code structure into Neo4j.

Parses source files using Tree-sitter AST and creates nodes/relationships
in the Neo4j dependency graph.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from drishti.graph.models import (
    ClassNode,
    DependencyEdge,
    FileNode,
    MethodNode,
    RelationType,
)
from drishti.utils.language import detect_language

if TYPE_CHECKING:
    from collections.abc import Iterator

    import tree_sitter

    from drishti.graph.client import GraphClient

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds a dependency graph from source code AST."""

    def __init__(self, client: GraphClient) -> None:
        """Initialize the graph builder.

        Args:
            client: Neo4j graph client.
        """
        self._client = client

    async def index_file(
        self,
        file_path: str,
        source_code: str,
        *,
        clear_existing: bool = True,
    ) -> dict[str, int]:
        """Index a source file into the dependency graph.

        Args:
            file_path: Path to the source file.
            source_code: Contents of the file.
            clear_existing: Whether to clear existing nodes for this file.

        Returns:
            Statistics about nodes created.
        """
        language = detect_language(file_path)
        if language == "unknown":
            logger.debug("Skipping unknown language file: %s", file_path)
            return {"skipped": 1}

        if clear_existing:
            await self._client.clear_graph(file_path)

        stats = {
            "files": 0,
            "packages": 0,
            "classes": 0,
            "methods": 0,
            "relationships": 0,
        }

        file_node = FileNode(
            id=file_path,
            name=Path(file_path).name,
            file_path=file_path,
            language=language,
            package=self._extract_package(file_path, language),
            start_line=1,
            end_line=source_code.count("\n") + 1,
        )
        await self._client.upsert_file(file_node)
        stats["files"] = 1

        try:
            parser = self._get_parser(language)
            if parser is None:
                return stats

            tree = parser.parse(source_code.encode())
            root = tree.root_node

            await self._extract_nodes(root, source_code.encode(), file_path, language, stats)
            await self._extract_dependencies(root, source_code.encode(), file_path, language, stats)

        except Exception:
            logger.exception("Error parsing %s", file_path)

        return stats

    async def index_directory(
        self,
        directory: str,
        *,
        extensions: list[str] | None = None,
    ) -> dict[str, int]:
        """Index all files in a directory.

        Args:
            directory: Path to directory.
            extensions: File extensions to include (e.g., [".py", ".java"]).

        Returns:
            Aggregate statistics.
        """
        from drishti.ingestion.gitignore import should_ignore

        if extensions is None:
            extensions = [".py", ".java", ".ts", ".tsx", ".js", ".jsx", ".go"]

        root = Path(directory)
        total_stats: dict[str, int] = {}

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue
            if should_ignore(str(file_path), str(root)):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                stats = await self.index_file(str(file_path), content)
                for key, value in stats.items():
                    total_stats[key] = total_stats.get(key, 0) + value
            except Exception:
                logger.exception("Failed to index %s", file_path)

        logger.info("Indexed directory %s: %s", directory, total_stats)
        return total_stats

    def _get_parser(self, language: str) -> tree_sitter.Parser | None:
        """Get a Tree-sitter parser for the language."""
        try:
            from tree_sitter import Language, Parser

            if language == "python":
                import tree_sitter_python as ts_lang
            elif language == "java":
                import tree_sitter_java as ts_lang
            elif language in ("typescript", "tsx"):
                import tree_sitter_typescript as ts_lang
            elif language in ("javascript", "jsx"):
                import tree_sitter_javascript as ts_lang
            elif language == "go":
                import tree_sitter_go as ts_lang
            else:
                return None

            lang = Language(ts_lang.language())
            parser = Parser(lang)
            return parser
        except ImportError:
            logger.warning("Tree-sitter language not available: %s", language)
            return None

    def _extract_package(self, file_path: str, language: str) -> str | None:
        """Extract package name from file path."""
        path = Path(file_path)

        if language == "python":
            parts = []
            current = path.parent
            while current.name and (current / "__init__.py").exists():
                parts.insert(0, current.name)
                current = current.parent
            return ".".join(parts) if parts else None

        if language == "java":
            return None

        return None

    async def _extract_nodes(
        self,
        root: tree_sitter.Node,
        source: bytes,
        file_path: str,
        language: str,
        stats: dict[str, int],
    ) -> None:
        """Extract class and method nodes from AST."""
        class_types = self._get_class_node_types(language)
        method_types = self._get_method_node_types(language)

        for node in self._walk_tree(root):
            if node.type in class_types:
                class_node = self._parse_class_node(node, source, file_path, language)
                if class_node:
                    await self._client.upsert_class(class_node)
                    stats["classes"] += 1

                    edge = DependencyEdge(
                        source_id=file_path,
                        target_id=class_node.id,
                        relation_type=RelationType.CONTAINS,
                    )
                    await self._client.create_relationship(edge)
                    stats["relationships"] += 1

            elif node.type in method_types:
                method_node = self._parse_method_node(node, source, file_path, language)
                if method_node:
                    await self._client.upsert_method(method_node)
                    stats["methods"] += 1

                    parent_id = method_node.parent_class or file_path
                    if method_node.parent_class:
                        parent_id = f"{file_path}:{method_node.parent_class}"

                    edge = DependencyEdge(
                        source_id=parent_id,
                        target_id=method_node.id,
                        relation_type=RelationType.CONTAINS,
                    )
                    await self._client.create_relationship(edge)
                    stats["relationships"] += 1

    async def _extract_dependencies(
        self,
        root: tree_sitter.Node,
        source: bytes,
        file_path: str,
        language: str,
        stats: dict[str, int],
    ) -> None:
        """Extract import and call dependencies."""
        import_types = self._get_import_node_types(language)
        call_types = self._get_call_node_types(language)

        for node in self._walk_tree(root):
            if node.type in import_types:
                imports = self._parse_imports(node, source, language)
                for imp in imports:
                    edge = DependencyEdge(
                        source_id=file_path,
                        target_id=imp,
                        relation_type=RelationType.DEPENDS_ON,
                        line_number=node.start_point[0] + 1,
                    )
                    await self._client.create_relationship(edge)
                    stats["relationships"] += 1

            elif node.type in call_types:
                call_info = self._parse_call(node, source, language)
                if call_info:
                    caller_id = self._find_enclosing_method(node, source, file_path, language)
                    if caller_id:
                        edge = DependencyEdge(
                            source_id=caller_id,
                            target_id=call_info,
                            relation_type=RelationType.CALLS,
                            line_number=node.start_point[0] + 1,
                        )
                        await self._client.create_relationship(edge)
                        stats["relationships"] += 1

    def _walk_tree(self, node: tree_sitter.Node) -> Iterator[tree_sitter.Node]:
        """Walk all nodes in the tree."""
        yield node
        for child in node.children:
            yield from self._walk_tree(child)

    def _get_class_node_types(self, language: str) -> set[str]:
        """Get AST node types that represent classes."""
        types = {
            "python": {"class_definition"},
            "java": {"class_declaration", "interface_declaration"},
            "typescript": {"class_declaration", "interface_declaration"},
            "javascript": {"class_declaration"},
            "go": {"type_declaration"},
        }
        return types.get(language, set())

    def _get_method_node_types(self, language: str) -> set[str]:
        """Get AST node types that represent methods/functions."""
        types = {
            "python": {"function_definition"},
            "java": {"method_declaration", "constructor_declaration"},
            "typescript": {"function_declaration", "method_definition", "arrow_function"},
            "javascript": {"function_declaration", "method_definition", "arrow_function"},
            "go": {"function_declaration", "method_declaration"},
        }
        return types.get(language, set())

    def _get_import_node_types(self, language: str) -> set[str]:
        """Get AST node types that represent imports."""
        types = {
            "python": {"import_statement", "import_from_statement"},
            "java": {"import_declaration"},
            "typescript": {"import_statement"},
            "javascript": {"import_statement"},
            "go": {"import_declaration"},
        }
        return types.get(language, set())

    def _get_call_node_types(self, language: str) -> set[str]:
        """Get AST node types that represent function calls."""
        types = {
            "python": {"call"},
            "java": {"method_invocation"},
            "typescript": {"call_expression"},
            "javascript": {"call_expression"},
            "go": {"call_expression"},
        }
        return types.get(language, set())

    def _parse_class_node(
        self,
        node: tree_sitter.Node,
        source: bytes,
        file_path: str,
        language: str,
    ) -> ClassNode | None:
        """Parse a class definition AST node."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = source[name_node.start_byte : name_node.end_byte].decode()

        docstring = None
        body = node.child_by_field_name("body")
        if body and body.children:
            first = body.children[0]
            if first.type == "expression_statement" and first.children:
                string_node = first.children[0]
                if string_node.type == "string":
                    docstring = source[string_node.start_byte : string_node.end_byte].decode()
                    docstring = docstring.strip("\"'")[:500]

        parent_classes = []
        superclass = node.child_by_field_name("superclass")
        if superclass:
            parent_classes.append(source[superclass.start_byte : superclass.end_byte].decode())

        return ClassNode(
            id=f"{file_path}:{name}",
            name=name,
            file_path=file_path,
            is_interface=node.type in {"interface_declaration"},
            docstring=docstring,
            parent_classes=parent_classes,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
        )

    def _parse_method_node(
        self,
        node: tree_sitter.Node,
        source: bytes,
        file_path: str,
        language: str,
    ) -> MethodNode | None:
        """Parse a method/function definition AST node."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = source[name_node.start_byte : name_node.end_byte].decode()

        parent_class = self._find_parent_class(node, source, language)

        params_node = node.child_by_field_name("parameters")
        parameters = []
        if params_node:
            params_text = source[params_node.start_byte : params_node.end_byte].decode()
            params_text = params_text.strip("()")
            if params_text:
                parameters = [p.strip().split(":")[0].strip() for p in params_text.split(",")]
                parameters = [p for p in parameters if p and p != "self" and p != "cls"]

        return_node = node.child_by_field_name("return_type")
        return_type = None
        if return_node:
            return_type = source[return_node.start_byte : return_node.end_byte].decode()

        is_async = False
        if language == "python":
            for child in node.children:
                if child.type == "async":
                    is_async = True
                    break

        docstring = None
        body = node.child_by_field_name("body")
        if body and body.children:
            first = body.children[0]
            if first.type == "expression_statement" and first.children:
                string_node = first.children[0]
                if string_node.type == "string":
                    docstring = source[string_node.start_byte : string_node.end_byte].decode()
                    docstring = docstring.strip("\"'")[:500]

        node_id = f"{file_path}:{parent_class}.{name}" if parent_class else f"{file_path}:{name}"

        return MethodNode(
            id=node_id,
            name=name,
            file_path=file_path,
            parent_class=parent_class,
            parameters=parameters,
            return_type=return_type,
            is_async=is_async,
            docstring=docstring,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
        )

    def _find_parent_class(
        self,
        node: tree_sitter.Node,
        source: bytes,
        language: str,
    ) -> str | None:
        """Find the enclosing class of a method node."""
        class_types = self._get_class_node_types(language)
        current = node.parent

        while current:
            if current.type in class_types:
                name_node = current.child_by_field_name("name")
                if name_node:
                    return source[name_node.start_byte : name_node.end_byte].decode()
            current = current.parent

        return None

    def _find_enclosing_method(
        self,
        node: tree_sitter.Node,
        source: bytes,
        file_path: str,
        language: str,
    ) -> str | None:
        """Find the enclosing method of a node."""
        method_types = self._get_method_node_types(language)
        current = node.parent

        while current:
            if current.type in method_types:
                name_node = current.child_by_field_name("name")
                if name_node:
                    method_name = source[name_node.start_byte : name_node.end_byte].decode()
                    parent_class = self._find_parent_class(current, source, language)
                    if parent_class:
                        return f"{file_path}:{parent_class}.{method_name}"
                    return f"{file_path}:{method_name}"
            current = current.parent

        return None

    def _parse_imports(
        self,
        node: tree_sitter.Node,
        source: bytes,
        language: str,
    ) -> list[str]:
        """Parse import statements and return imported module names."""
        imports: list[str] = []

        if language == "python":
            if node.type == "import_from_statement":
                module_node = node.child_by_field_name("module_name")
                if module_node:
                    imports.append(source[module_node.start_byte : module_node.end_byte].decode())
            elif node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        imports.append(source[child.start_byte : child.end_byte].decode())

        return imports

    def _parse_call(
        self,
        node: tree_sitter.Node,
        source: bytes,
        language: str,
    ) -> str | None:
        """Parse a function call and return the callee name."""
        func_node = node.child_by_field_name("function")
        if not func_node:
            return None

        return source[func_node.start_byte : func_node.end_byte].decode()
