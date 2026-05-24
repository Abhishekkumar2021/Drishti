"""Unit tests for programming language detection."""

from __future__ import annotations

import pytest

from drishti.utils.language import LanguageRegistry

pytestmark = pytest.mark.unit


class TestLanguageRegistry:
    def test_detects_python_by_extension(self) -> None:
        registry = LanguageRegistry()
        assert registry.detect("src/main.py") == "python"

    def test_detects_typescript_by_extension(self) -> None:
        registry = LanguageRegistry()
        assert registry.detect("components/App.tsx") == "typescript"

    def test_detects_python_from_shebang(self) -> None:
        registry = LanguageRegistry()
        content = b"#!/usr/bin/env python3\nprint('hello')\n"
        assert registry.detect("scripts/deploy", content) == "python"

    def test_detects_java_from_class_magic_bytes(self) -> None:
        registry = LanguageRegistry()
        content = b"\xca\xfe\xba\xbe" + b"\x00" * 20
        assert registry.detect("build/App.class", content) == "java"

    def test_returns_none_for_unknown_extension(self) -> None:
        registry = LanguageRegistry()
        assert registry.detect("README.md") is None

    def test_has_parser_extension_when_parser_registered(self) -> None:
        registry = LanguageRegistry()
        assert registry.has_parser_extension("src/main.py", frozenset({".py"}))
        assert not registry.has_parser_extension("src/main.py", frozenset({".java"}))

    def test_custom_language_registration(self) -> None:
        registry = LanguageRegistry()
        registry.register("kotlin", [".kt"])
        assert registry.detect("Service.kt") == "kotlin"
