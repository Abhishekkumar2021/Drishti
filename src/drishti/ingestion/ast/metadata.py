"""AST symbol metadata enrichment (US-03.07)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node

_NESTED_DEFINITION_TYPES: dict[str, frozenset[str]] = {
    "python": frozenset({"function_definition", "class_definition"}),
    "java": frozenset(
        {
            "method_declaration",
            "constructor_declaration",
            "class_declaration",
            "interface_declaration",
        }
    ),
    "javascript": frozenset(
        {"function_declaration", "method_definition", "class_declaration", "arrow_function"}
    ),
    "typescript": frozenset(
        {
            "function_declaration",
            "method_definition",
            "class_declaration",
            "arrow_function",
            "interface_declaration",
        }
    ),
    "go": frozenset({"function_declaration", "method_declaration", "type_declaration"}),
}

_CYCLOMATIC_NODE_TYPES: dict[str, frozenset[str]] = {
    "python": frozenset(
        {
            "if_statement",
            "elif_clause",
            "for_statement",
            "while_statement",
            "except_clause",
            "with_statement",
            "conditional_expression",
            "boolean_operator",
            "match_statement",
            "case_clause",
        }
    ),
    "java": frozenset(
        {
            "if_statement",
            "for_statement",
            "enhanced_for_statement",
            "while_statement",
            "do_statement",
            "catch_clause",
            "switch_expression",
            "ternary_expression",
            "case",
        }
    ),
    "javascript": frozenset(
        {
            "if_statement",
            "for_statement",
            "for_in_statement",
            "while_statement",
            "do_statement",
            "catch_clause",
            "switch_statement",
            "switch_case",
            "ternary_expression",
        }
    ),
    "typescript": frozenset(
        {
            "if_statement",
            "for_statement",
            "for_in_statement",
            "while_statement",
            "do_statement",
            "catch_clause",
            "switch_statement",
            "switch_case",
            "ternary_expression",
        }
    ),
    "go": frozenset(
        {
            "if_statement",
            "for_statement",
            "switch_statement",
            "case_clause",
            "select_statement",
            "communication_case",
        }
    ),
}

_EXECUTABLE_NODE_TYPES = frozenset(
    {
        "function_definition",
        "method_declaration",
        "constructor_declaration",
        "function_declaration",
        "method_definition",
        "arrow_function",
    }
)


@dataclass(frozen=True)
class EnrichedSymbolMetadata:
    """Structured metadata attached to a code chunk."""

    docstring: str | None = None
    parameters: tuple[str, ...] = ()
    return_type: str | None = None
    cyclomatic_complexity: int | None = None
    parent_module: str | None = None
    context_path: str | None = None
    definition_file_path: str | None = None


def enrich_symbol_metadata(
    *,
    definition_node: Node,
    source: bytes,
    language: str,
    file_path: str,
    symbol_name: str,
    package_name: str | None,
    parent_class: str | None,
) -> EnrichedSymbolMetadata:
    """Extract docstrings, signatures, complexity, and structural paths for a symbol."""
    parent_module = resolve_parent_module(file_path, package_name)
    context_path = build_context_path(
        file_path=file_path,
        symbol_name=symbol_name,
        parent_class=parent_class,
        parent_module=parent_module,
    )
    docstring = extract_docstring(definition_node, source, language)
    parameters = tuple(extract_parameters(definition_node, source, language))
    return_type = extract_return_type(definition_node, source, language)
    complexity = (
        compute_cyclomatic_complexity(definition_node, language)
        if definition_node.type in _EXECUTABLE_NODE_TYPES
        else None
    )
    return EnrichedSymbolMetadata(
        docstring=docstring,
        parameters=parameters,
        return_type=return_type,
        cyclomatic_complexity=complexity,
        parent_module=parent_module,
        context_path=context_path,
        definition_file_path=file_path,
    )


def resolve_parent_module(file_path: str, package_name: str | None) -> str | None:
    """Return a module or package identifier for the chunk's file."""
    if package_name:
        return package_name
    path = Path(file_path)
    if path.suffix:
        path = path.with_suffix("")
    parts = list(path.parts)
    if not parts:
        return None
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_context_path(
    *,
    file_path: str,
    symbol_name: str,
    parent_class: str | None,
    parent_module: str | None,
) -> str:
    """Build a fully qualified structural path for retrieval tracing."""
    if parent_class:
        return f"{file_path}::{parent_class}::{symbol_name}"
    if parent_module:
        return f"{file_path}::{parent_module}::{symbol_name}"
    return f"{file_path}::{symbol_name}"


def extract_docstring(definition_node: Node, source: bytes, language: str) -> str | None:
    """Return documentation text associated with a symbol."""
    if language == "python":
        return _python_docstring(definition_node, source)
    if language in {"javascript", "typescript"}:
        return _leading_comment_docstring(definition_node, source)
    if language == "java":
        return _java_docstring(definition_node, source)
    if language == "go":
        return _leading_comment_docstring(definition_node, source)
    return None


def extract_parameters(definition_node: Node, source: bytes, language: str) -> list[str]:
    """Return human-readable parameter descriptors for a callable symbol."""
    params_node = definition_node.child_by_field_name("parameters")
    if params_node is None and language == "go":
        params_node = _go_parameter_list(definition_node)
    if params_node is None:
        return []

    parameters: list[str] = []
    for child in params_node.children:
        if child.type in {"(", ")", ",", "comment"}:
            continue
        if child.type in {"formal_parameters", "parameter_list"}:
            parameters.extend(extract_parameters_from_node(child, source))
            continue
        text = _node_text(source, child).strip()
        if text and text not in {",", "(", ")"}:
            parameters.append(text)
    return parameters


def extract_parameters_from_node(params_node: Node, source: bytes) -> list[str]:
    """Flatten a parameter list node into descriptor strings."""
    parameters: list[str] = []
    for child in params_node.children:
        if child.type in {"(", ")", ",", "comment"}:
            continue
        text = _node_text(source, child).strip()
        if text and text not in {",", "(", ")"}:
            parameters.append(text)
    return parameters


def extract_return_type(definition_node: Node, source: bytes, language: str) -> str | None:
    """Return the declared return type for a callable symbol when available."""
    if language == "java":
        type_node = definition_node.child_by_field_name("type")
        if type_node is not None:
            return _node_text(source, type_node).strip()
        return None

    return_node = definition_node.child_by_field_name("return_type")
    if return_node is not None:
        return _node_text(source, return_node).strip()

    if language == "go":
        result_node = definition_node.child_by_field_name("result")
        if result_node is not None:
            return _node_text(source, result_node).strip()

    return None


def compute_cyclomatic_complexity(definition_node: Node, language: str) -> int:
    """Calculate McCabe cyclomatic complexity for a symbol body."""
    body = _body_node(definition_node)
    if body is None:
        return 1

    decision_types = _CYCLOMATIC_NODE_TYPES.get(language, frozenset())
    nested_types = _NESTED_DEFINITION_TYPES.get(language, frozenset())
    complexity = 1
    stack: list[Node] = [body]
    while stack:
        current = stack.pop()
        if current is not definition_node and current.type in nested_types:
            continue
        if current.type in decision_types:
            complexity += 1
        stack.extend(current.children)
    return complexity


def _body_node(definition_node: Node) -> Node | None:
    for field_name in ("body", "block"):
        body = definition_node.child_by_field_name(field_name)
        if body is not None:
            return body
    return None


def _python_docstring(definition_node: Node, source: bytes) -> str | None:
    body = definition_node.child_by_field_name("body")
    if body is None or body.named_child_count == 0:
        return _leading_comment_docstring(definition_node, source)
    first = body.named_children[0]
    if first.type != "expression_statement":
        return None
    expr = first.children[0] if first.children else None
    if expr is None or expr.type != "string":
        return None
    return _decode_python_string(_node_text(source, expr))


def _java_docstring(definition_node: Node, source: bytes) -> str | None:
    for child in definition_node.children:
        if child.type == "block_comment":
            text = _node_text(source, child).strip()
            if text.startswith("/**"):
                return _strip_javadoc(text)
    return _leading_comment_docstring(definition_node, source)


def _leading_comment_docstring(definition_node: Node, source: bytes) -> str | None:
    current = definition_node.prev_named_sibling
    comments: list[str] = []
    while current is not None and current.type in {"comment", "block_comment"}:
        comments.insert(0, _node_text(source, current).strip())
        current = current.prev_named_sibling
    if not comments:
        return None
    combined = "\n".join(comments)
    if combined.startswith("/**"):
        return _strip_javadoc(combined)
    return combined.lstrip("/").strip() or None


def _strip_javadoc(raw: str) -> str:
    text = raw.strip()
    if text.startswith("/**"):
        text = text[3:]
    if text.endswith("*/"):
        text = text[:-2]
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("*"):
            stripped = stripped[1:].strip()
        lines.append(stripped)
    return "\n".join(lines).strip()


def _decode_python_string(raw: str) -> str:
    text = raw.strip()
    if len(text) >= 6 and text[:3] in {'"""', "'''"}:
        return text[3:-3].strip()
    if len(text) >= 2 and text[0] in {'"', "'"}:
        return text[1:-1].strip()
    return text


def _go_parameter_list(definition_node: Node) -> Node | None:
    for child in definition_node.children:
        if child.type == "parameter_list":
            return child
    return None


def collect_imported_symbols(root: Node, source: bytes, language: str) -> list[str]:
    """Collect imported symbol names and module paths from a file."""
    if language == "python":
        return _python_imported_symbols(root, source)
    if language == "java":
        return _java_imported_symbols(root, source)
    if language in {"javascript", "typescript"}:
        return _ecmascript_imported_symbols(root, source)
    if language == "go":
        return _go_imported_symbols(root, source)
    return []


def _python_imported_symbols(root: Node, source: bytes) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        if value and value not in seen:
            seen.add(value)
            symbols.append(value)

    stack = [root]
    while stack:
        node = stack.pop()
        if node.type == "import_statement":
            for child in node.children:
                if child.type in {"dotted_name", "aliased_import"}:
                    add(_node_text(source, child).strip())
        elif node.type == "import_from_statement":
            module = node.child_by_field_name("module_name")
            if module is not None:
                add(_node_text(source, module).strip())
            for child in node.children:
                if child.type in {"dotted_name", "aliased_import"}:
                    add(_node_text(source, child).strip().lstrip("."))
        stack.extend(node.children)
    return sorted(symbols)


def _java_imported_symbols(root: Node, source: bytes) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    for child in root.children:
        if child.type != "import_declaration":
            continue
        scoped = child.child_by_field_name("scoped_identifier")
        if scoped is None:
            for nested in child.children:
                if nested.type == "scoped_identifier":
                    scoped = nested
                    break
        if scoped is not None:
            value = _node_text(source, scoped).strip()
            if value not in seen:
                seen.add(value)
                symbols.append(value)
    return symbols


def _ecmascript_imported_symbols(root: Node, source: bytes) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type == "import_statement":
            text = _node_text(source, node)
            for match in _ECMASCRIPT_IMPORT_PATH_RE.finditer(text):
                path = match.group(1)
                if path not in seen:
                    seen.add(path)
                    symbols.append(path)
            for match in _ECMASCRIPT_NAMED_IMPORT_RE.finditer(text):
                named = match.group(1)
                default = match.group(2)
                if named:
                    for part in named.split(","):
                        symbol = part.strip().split(" as ", maxsplit=1)[0].strip()
                        if symbol and symbol not in seen:
                            seen.add(symbol)
                            symbols.append(symbol)
                elif default and default not in seen:
                    seen.add(default)
                    symbols.append(default)
        stack.extend(node.children)
    return sorted(symbols)


def _go_imported_symbols(root: Node, source: bytes) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    for child in root.children:
        if child.type != "import_declaration":
            continue
        stack = [child]
        while stack:
            node = stack.pop()
            if node.type == "import_spec":
                path_node = node.child_by_field_name("path")
                if path_node is not None:
                    value = _node_text(source, path_node).strip().strip('"').strip("`")
                    if value not in seen:
                        seen.add(value)
                        symbols.append(value)
                name_node = node.child_by_field_name("name")
                if name_node is not None:
                    value = _node_text(source, name_node).strip()
                    if value not in seen:
                        seen.add(value)
                        symbols.append(value)
            stack.extend(node.children)
    return sorted(symbols)


_ECMASCRIPT_IMPORT_PATH_RE = re.compile(r"""from\s+['"]([^'"]+)['"]""")
_ECMASCRIPT_NAMED_IMPORT_RE = re.compile(r"""import\s+(?:type\s+)?(?:\{([^}]+)\}|(\w+))""")


def _node_text(source: bytes, node: Node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
