"""Go Tree-sitter parser (US-03.05)."""

from __future__ import annotations

import tree_sitter_go as tsgo
from tree_sitter import Language, Node

from drishti.ingestion.ast.base import TreeSitterParser
from drishti.ingestion.ast.rules import ParserRules, load_parser_rules

_GO_EXTENSIONS = (".go",)
_LANGUAGE = "go"
_PARSE_CONTEXT_IMPORTS = "module_imports"


class GoParser(TreeSitterParser):
    """Extracts Go packages, types, functions, and methods into universal chunks."""

    @classmethod
    def from_package(cls) -> GoParser:
        """Build a parser using the packaged Go query file."""
        return cls.from_rules(load_parser_rules())

    @classmethod
    def from_rules(cls, rules: ParserRules) -> GoParser:
        """Build a parser using rule-driven query and thresholds."""
        language = Language(tsgo.language())
        return cls(
            language,
            cls.load_query(rules.query_file_for(_LANGUAGE)),
            language_name=_LANGUAGE,
            min_chunk_lines=rules.min_chunk_lines_for(_LANGUAGE),
        )

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """File extensions handled by this parser."""
        return _GO_EXTENSIONS

    def _prepare_parse_context(self, root: Node, source: bytes) -> dict[str, object]:
        return {_PARSE_CONTEXT_IMPORTS: self._collect_imports(root, source)}

    def _symbol_chunk_metadata(
        self,
        definition_node: Node,
        source: bytes,
        parse_context: dict[str, object],
    ) -> dict[str, object]:
        imports = parse_context.get(_PARSE_CONTEXT_IMPORTS, [])
        module_imports = imports if isinstance(imports, list) else []
        metadata: dict[str, object] = {"dependencies": list(module_imports)}
        if definition_node.type == "method_declaration":
            receiver_type = self._method_receiver_type(definition_node, source)
            if receiver_type is not None:
                metadata["parent_class"] = receiver_type
        return metadata

    @classmethod
    def _extract_package_name(cls, root: Node, source: bytes) -> str | None:
        for child in root.children:
            if child.type != "package_clause":
                continue
            for nested in child.children:
                if nested.type == "package_identifier":
                    return cls._node_text(source, nested)
        return None

    @classmethod
    def _collect_imports(cls, root: Node, source: bytes) -> list[str]:
        imports: list[str] = []
        seen: set[str] = set()
        for child in root.children:
            if child.type != "import_declaration":
                continue
            for import_path in cls._paths_from_import_declaration(child, source):
                if import_path not in seen:
                    seen.add(import_path)
                    imports.append(import_path)
        return sorted(imports)

    @classmethod
    def _paths_from_import_declaration(cls, import_node: Node, source: bytes) -> list[str]:
        paths: list[str] = []
        stack = [import_node]
        while stack:
            node = stack.pop()
            if node.type == "import_spec":
                path = cls._import_path_from_spec(node, source)
                if path:
                    paths.append(path)
            stack.extend(node.children)
        return paths

    @classmethod
    def _import_path_from_spec(cls, spec_node: Node, source: bytes) -> str | None:
        path_node = spec_node.child_by_field_name("path")
        if path_node is None:
            return None
        raw = cls._node_text(source, path_node).strip()
        return raw.strip('"').strip("`")

    @classmethod
    def _method_receiver_type(cls, method_node: Node, source: bytes) -> str | None:
        receiver = method_node.child_by_field_name("receiver")
        if receiver is None:
            return None
        stack = [receiver]
        while stack:
            current = stack.pop()
            if current.type == "type_identifier":
                return cls._node_text(source, current)
            stack.extend(current.children)
        return None

    @classmethod
    def is_interface_type(cls, definition_node: Node, _source: bytes) -> bool:
        """Return whether a type declaration defines an interface."""
        if definition_node.type != "type_declaration":
            return False
        stack = [definition_node]
        while stack:
            current = stack.pop()
            if current.type == "interface_type":
                return True
            stack.extend(current.children)
        return False

    @classmethod
    def is_struct_type(cls, definition_node: Node, _source: bytes) -> bool:
        """Return whether a type declaration defines a struct."""
        if definition_node.type != "type_declaration":
            return False
        stack = [definition_node]
        while stack:
            current = stack.pop()
            if current.type == "struct_type":
                return True
            stack.extend(current.children)
        return False
