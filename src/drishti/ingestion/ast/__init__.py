"""AST-aware code parsers built on Tree-sitter."""

from drishti.ingestion.ast.base import TreeSitterParser
from drishti.ingestion.ast.catalog import (
    PARSER_CATALOG,
    build_production_parsers,
    supported_parser_extensions,
)
from drishti.ingestion.ast.ecmascript import EcmaScriptParser
from drishti.ingestion.ast.go import GoParser
from drishti.ingestion.ast.java import JavaParser
from drishti.ingestion.ast.javascript import JavaScriptParser
from drishti.ingestion.ast.python import PythonParser
from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.ast.rules import LanguageRule, ParserRules, load_parser_rules
from drishti.ingestion.ast.typescript import TypeScriptParser

__all__ = [
    "PARSER_CATALOG",
    "EcmaScriptParser",
    "GoParser",
    "JavaParser",
    "JavaScriptParser",
    "LanguageRule",
    "ParserRules",
    "PythonParser",
    "TreeSitterParser",
    "TypeScriptParser",
    "build_production_parsers",
    "create_default_parser_registry",
    "load_parser_rules",
    "supported_parser_extensions",
]
