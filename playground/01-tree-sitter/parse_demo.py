#!/usr/bin/env python3
"""Tree-sitter AST Parsing Demo.

This script demonstrates how Drishti uses Tree-sitter to parse code
into Abstract Syntax Trees for semantic chunking.

Run with: uv run python playground/01-tree-sitter/parse_demo.py
"""

from __future__ import annotations

import tree_sitter_python as ts_python
from tree_sitter import Language, Parser

# Sample Python code to parse
SAMPLE_CODE = '''
"""Authentication module for user login."""

import hashlib
from datetime import datetime


class AuthenticationService:
    """Handles user authentication and session management."""

    def __init__(self, secret_key: str):
        """Initialize with secret key for token signing."""
        self.secret_key = secret_key
        self._sessions: dict[str, datetime] = {}

    def authenticate(self, username: str, password: str) -> bool:
        """Verify user credentials against the database.

        Args:
            username: The user's login name.
            password: The plaintext password to verify.

        Returns:
            True if credentials are valid, False otherwise.
        """
        hashed = self._hash_password(password)
        # In real code, this would check against a database
        return hashed is not None

    def _hash_password(self, password: str) -> str:
        """Create a salted hash of the password."""
        return hashlib.sha256(
            (password + self.secret_key).encode()
        ).hexdigest()


def create_token(user_id: str) -> str:
    """Generate a JWT token for the authenticated user."""
    return f"token_{user_id}"
'''


def main() -> None:
    """Run the Tree-sitter parsing demo."""
    print("=" * 60)
    print("Tree-sitter AST Parsing Demo")
    print("=" * 60)

    # Initialize the parser with Python language
    python_lang = Language(ts_python.language())
    parser = Parser(python_lang)

    # Parse the source code
    tree = parser.parse(SAMPLE_CODE.encode())
    root = tree.root_node

    print("\n1. FULL SYNTAX TREE (S-expression)")
    print("-" * 40)
    print(root.sexp()[:500] + "...")

    print("\n2. ROOT NODE CHILDREN")
    print("-" * 40)
    for i, child in enumerate(root.children):
        print(f"  [{i}] {child.type}: lines {child.start_point[0]+1}-{child.end_point[0]+1}")

    print("\n3. EXTRACTED FUNCTIONS")
    print("-" * 40)
    extract_functions(root, SAMPLE_CODE.encode())

    print("\n4. EXTRACTED CLASSES")
    print("-" * 40)
    extract_classes(root, SAMPLE_CODE.encode())

    print("\n5. WHY THIS MATTERS FOR RAG")
    print("-" * 40)
    print("""
When we index code for RAG:

❌ NAIVE CHUNKING (500 chars):
   - Splits authenticate() in half
   - Loses docstring context
   - Breaks class-method relationship

✅ AST-AWARE CHUNKING:
   - Complete AuthenticationService class as one chunk
   - Each method with its docstring
   - Preserves semantic structure for better retrieval
""")


def extract_functions(node, source: bytes) -> None:
    """Recursively extract all function definitions."""
    if node.type == "function_definition":
        name_node = node.child_by_field_name("name")
        name = source[name_node.start_byte:name_node.end_byte].decode() if name_node else "<anon>"

        # Get parameters
        params_node = node.child_by_field_name("parameters")
        params = source[params_node.start_byte:params_node.end_byte].decode() if params_node else "()"

        # Get return type if present
        return_node = node.child_by_field_name("return_type")
        return_type = source[return_node.start_byte:return_node.end_byte].decode() if return_node else "None"

        # Get docstring if present
        docstring = ""
        body = node.child_by_field_name("body")
        if body and body.children:
            first_stmt = body.children[0]
            if first_stmt.type == "expression_statement":
                string_node = first_stmt.children[0] if first_stmt.children else None
                if string_node and string_node.type == "string":
                    docstring = source[string_node.start_byte:string_node.end_byte].decode()
                    docstring = docstring[:50] + "..." if len(docstring) > 50 else docstring

        print(f"  def {name}{params} -> {return_type}")
        print(f"      Lines: {node.start_point[0]+1}-{node.end_point[0]+1}")
        if docstring:
            print(f"      Docstring: {docstring}")
        print()

    for child in node.children:
        extract_functions(child, source)


def extract_classes(node, source: bytes) -> None:
    """Extract all class definitions with their methods."""
    if node.type == "class_definition":
        name_node = node.child_by_field_name("name")
        name = source[name_node.start_byte:name_node.end_byte].decode() if name_node else "<anon>"

        # Find body and count methods
        body = node.child_by_field_name("body")
        method_count = 0
        if body:
            for child in body.children:
                if child.type == "function_definition":
                    method_count += 1

        print(f"  class {name}:")
        print(f"      Lines: {node.start_point[0]+1}-{node.end_point[0]+1}")
        print(f"      Methods: {method_count}")
        print()

    for child in node.children:
        extract_classes(child, source)


if __name__ == "__main__":
    main()
