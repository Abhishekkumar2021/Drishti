"""Shared ECMAScript (JavaScript / TypeScript) Tree-sitter parsing."""

from __future__ import annotations

import re
from typing import ClassVar

from tree_sitter import Node

from drishti.ingestion.ast.base import TreeSitterParser

_IMPORT_FROM_RE = re.compile(
    r"""import\s+(?:type\s+)?(?:[^'";]+?\s+from\s+)?['"]([^'"]+)['"]""",
)
_IMPORT_SIDE_EFFECT_RE = re.compile(r"""import\s*['"]([^'"]+)['"]""")
_HOOK_NAME_RE = re.compile(r"^use[A-Z]")
_PARSE_CONTEXT_IMPORTS = "module_imports"


class EcmaScriptParser(TreeSitterParser):
    """Extracts JS/TS symbols with export and module metadata."""

    _ENCLOSING_SCOPE_TYPES: ClassVar[tuple[str, ...]] = ("class_declaration",)

    def _prepare_parse_context(self, root: Node, source: bytes) -> dict[str, object]:
        context = super()._prepare_parse_context(root, source)
        module_imports = self._collect_module_imports(root, source)
        file_symbols = context.get("imported_symbols", [])
        symbol_set = set(file_symbols) if isinstance(file_symbols, list) else set()
        merged_symbols = sorted(symbol_set | set(module_imports))
        return {
            **context,
            _PARSE_CONTEXT_IMPORTS: module_imports,
            "imported_symbols": merged_symbols,
        }

    def _symbol_chunk_metadata(
        self,
        definition_node: Node,
        source: bytes,
        parse_context: dict[str, object],
    ) -> dict[str, object]:
        imports = parse_context.get(_PARSE_CONTEXT_IMPORTS, [])
        module_imports = imports if isinstance(imports, list) else []
        return {
            "exports": self._extract_exports(definition_node, source),
            "dependencies": list(module_imports),
        }

    @classmethod
    def _resolve_span_node(cls, definition_node: Node) -> Node:
        parent = definition_node.parent
        if parent is not None and parent.type == "export_statement":
            return parent
        return super()._resolve_span_node(definition_node)

    @classmethod
    def _extract_exports(cls, definition_node: Node, source: bytes) -> list[str]:
        exports: list[str] = []
        current = definition_node.parent
        while current is not None:
            if current.type == "export_statement":
                exports.extend(cls._export_modifiers_from_statement(current, source))
                break
            current = current.parent
        return exports

    @classmethod
    def _export_modifiers_from_statement(cls, export_node: Node, source: bytes) -> list[str]:
        modifiers: list[str] = []
        for child in export_node.children:
            if child.type == "export":
                modifiers.append("export")
            elif child.type == "default":
                modifiers.append("default")
        if not modifiers:
            text = cls._node_text(source, export_node)
            if text.startswith("export"):
                modifiers.append("export")
            if "default" in text.split():
                modifiers.append("default")
        return modifiers

    @classmethod
    def _collect_module_imports(cls, root: Node, source: bytes) -> list[str]:
        imports: list[str] = []
        seen: set[str] = set()
        stack = [root]
        while stack:
            node = stack.pop()
            if node.type == "import_statement":
                module_path = cls._module_path_from_import(node, source)
                if module_path and module_path not in seen:
                    seen.add(module_path)
                    imports.append(module_path)
            stack.extend(node.children)
        return sorted(imports)

    @classmethod
    def _module_path_from_import(cls, import_node: Node, source: bytes) -> str | None:
        text = cls._node_text(source, import_node)
        match = _IMPORT_FROM_RE.search(text)
        if match is None:
            match = _IMPORT_SIDE_EFFECT_RE.search(text)
        if match is None:
            return None
        return match.group(1)

    @staticmethod
    def is_react_hook(symbol_name: str, node_type: str) -> bool:
        """Return whether a function symbol matches React hook naming conventions."""
        return node_type == "function_declaration" and bool(_HOOK_NAME_RE.match(symbol_name))
