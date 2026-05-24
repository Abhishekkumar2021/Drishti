"""Java Tree-sitter parser (US-03.03)."""

from __future__ import annotations

from typing import ClassVar

import tree_sitter_java as tsjava
from tree_sitter import Language, Node

from drishti.ingestion.ast.base import TreeSitterParser

_JAVA_EXTENSIONS = (".java",)
_QUERY_FILE = "java.scm"
_ANNOTATION_NODE_TYPES = frozenset({"marker_annotation", "annotation"})


class JavaParser(TreeSitterParser):
    """Extracts Java packages, types, fields, and methods into universal chunks."""

    _ENCLOSING_SCOPE_TYPES: ClassVar[tuple[str, ...]] = (
        "class_declaration",
        "interface_declaration",
    )

    @classmethod
    def from_package(cls) -> JavaParser:
        """Build a parser using the packaged Java query file."""
        language = Language(tsjava.language())
        return cls(language, cls.load_query(_QUERY_FILE), language_name="java")

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions handled by this parser."""
        return _JAVA_EXTENSIONS

    @classmethod
    def _extract_package_name(cls, root: Node, source: bytes) -> str | None:
        for child in root.children:
            if child.type != "package_declaration":
                continue
            package_node = child.child_by_field_name("name")
            if package_node is not None:
                return cls._node_text(source, package_node)
            scoped = child.child_by_field_name("scoped_identifier")
            if scoped is not None:
                return cls._node_text(source, scoped)
            for nested in child.children:
                if nested.type == "scoped_identifier":
                    return cls._node_text(source, nested)
        return None

    @classmethod
    def _extract_decorators(cls, definition_node: Node, source: bytes) -> list[str]:
        modifiers = cls._find_modifiers_node(definition_node)
        if modifiers is None:
            return []
        annotations: list[str] = []
        for child in modifiers.children:
            if child.type not in _ANNOTATION_NODE_TYPES:
                continue
            raw = cls._node_text(source, child).strip()
            annotations.append(cls._normalize_annotation(raw))
        return annotations

    @classmethod
    def _find_modifiers_node(cls, definition_node: Node) -> Node | None:
        for child in definition_node.children:
            if child.type == "modifiers":
                return child
        return None
