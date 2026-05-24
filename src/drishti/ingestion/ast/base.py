"""Tree-sitter AST parser base class."""

from __future__ import annotations

import hashlib
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from importlib import resources

from tree_sitter import Language, Node, Parser, Query, QueryCursor

from drishti.api.schemas import UniversalChunk
from drishti.ingestion.base import BaseParser


class TreeSitterParser(BaseParser, ABC):
    """Language-agnostic Tree-sitter parser using query captures."""

    _CHUNK_NODE_CAPTURE = "chunk_node"

    def __init__(
        self,
        language: Language,
        query_scm: str,
        *,
        language_name: str,
    ) -> None:
        """Initialize parser with a Tree-sitter language and query.

        Args:
            language: Compiled Tree-sitter language.
            query_scm: Query source (S-expression).
            language_name: Human-readable language label for chunks.

        """
        self._language_name = language_name
        self._parser = Parser(language)
        self._query = Query(language, query_scm)

    @classmethod
    @abstractmethod
    def from_package(cls) -> TreeSitterParser:
        """Construct a parser using packaged grammar and query assets."""
        raise NotImplementedError

    @staticmethod
    def load_query(relative_name: str) -> str:
        """Load a Tree-sitter query file bundled with the ingestion package."""
        package = "drishti.ingestion.queries"
        try:
            query_file = resources.files(package).joinpath(relative_name)
        except (ModuleNotFoundError, TypeError) as exc:
            msg = f"Could not resolve query package {package!r}"
            raise FileNotFoundError(msg) from exc
        if not query_file.is_file():
            msg = f"Tree-sitter query file not found: {relative_name}"
            raise FileNotFoundError(msg)
        return query_file.read_text(encoding="utf-8")

    def parse(
        self,
        file_content: bytes,
        file_path: str,
        *,
        last_modified: datetime | None = None,
    ) -> list[UniversalChunk]:
        """Parse source bytes into universal chunks for each captured symbol."""
        if not file_content:
            return []

        tree = self._parser.parse(file_content)
        cursor = QueryCursor(self._query)
        seen_spans: set[tuple[int, int, str]] = set()
        chunks: list[UniversalChunk] = []
        source_id = hashlib.sha256(file_content).hexdigest()
        indexed_at = last_modified if last_modified is not None else datetime.now(UTC)

        for _pattern_index, capture_map in cursor.matches(tree.root_node):
            for definition_node in capture_map.get(self._CHUNK_NODE_CAPTURE, []):
                if self._has_error_descendant(definition_node):
                    continue

                name_node = definition_node.child_by_field_name("name")
                if name_node is None:
                    continue

                symbol_name = self._node_text(file_content, name_node)
                span_node, decorators = self._chunk_span(definition_node, file_content)
                span_key = (span_node.start_byte, span_node.end_byte, definition_node.type)
                if span_key in seen_spans:
                    continue
                seen_spans.add(span_key)

                chunks.append(
                    self._build_chunk(
                        file_content=file_content,
                        file_path=file_path,
                        definition_node=definition_node,
                        span_node=span_node,
                        symbol_name=symbol_name,
                        decorators=decorators,
                        source_id=source_id,
                        indexed_at=indexed_at,
                    )
                )

        return sorted(chunks, key=lambda chunk: (chunk.start_line or 0, chunk.name or ""))

    def _build_chunk(
        self,
        *,
        file_content: bytes,
        file_path: str,
        definition_node: Node,
        span_node: Node,
        symbol_name: str,
        decorators: list[str],
        source_id: str,
        indexed_at: datetime,
    ) -> UniversalChunk:
        content = self._node_text(file_content, span_node)
        start_line = span_node.start_point[0] + 1
        end_line = self._inclusive_end_line(span_node)
        parent_class = self._enclosing_class_name(definition_node, file_content)

        return UniversalChunk(
            id=str(uuid.uuid4()),
            source_id=source_id,
            content=content,
            content_type="code",
            file_path=file_path,
            source_type="git_repo",
            language=self._language_name,
            start_line=start_line,
            end_line=end_line,
            page_number=None,
            node_type=definition_node.type,
            name=symbol_name,
            parent_class=parent_class,
            decorators=decorators,
            last_modified=indexed_at,
        )

    @staticmethod
    def _inclusive_end_line(node: Node) -> int:
        """Return the 1-indexed inclusive end line for a syntax node."""
        end_row, end_column = node.end_point
        # Tree-sitter end_point is exclusive; column 0 means the node ends at a line break.
        if end_column == 0:
            return end_row
        return end_row + 1

    @staticmethod
    def _node_text(source: bytes, node: Node) -> str:
        return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")

    @classmethod
    def _chunk_span(cls, definition_node: Node, source: bytes) -> tuple[Node, list[str]]:
        parent = definition_node.parent
        if parent is not None and parent.type == "decorated_definition":
            return parent, cls._extract_decorators(parent, source)
        return definition_node, []

    @classmethod
    def _extract_decorators(cls, decorated_node: Node, source: bytes) -> list[str]:
        decorators: list[str] = []
        for child in decorated_node.children:
            if child.type != "decorator":
                continue
            raw = cls._node_text(source, child).strip()
            decorators.append(cls._normalize_decorator(raw))
        return decorators

    @staticmethod
    def _normalize_decorator(raw: str) -> str:
        text = raw.lstrip("@").strip()
        if "(" in text:
            return text.split("(", maxsplit=1)[0].strip()
        return text

    @classmethod
    def _enclosing_class_name(cls, node: Node, source: bytes) -> str | None:
        current = node.parent
        while current is not None:
            if current.type == "class_definition":
                name_node = current.child_by_field_name("name")
                if name_node is not None:
                    return cls._node_text(source, name_node)
                return None
            current = current.parent
        return None

    @staticmethod
    def _has_error_descendant(node: Node) -> bool:
        """Return True when the node subtree contains a Tree-sitter ERROR node."""
        stack = [node]
        while stack:
            current = stack.pop()
            if current.type == "ERROR":
                return True
            stack.extend(current.children)
        return False
