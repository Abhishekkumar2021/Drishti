"""Programming language detection and extension registry."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SUPPORTED_LANGUAGES = frozenset(
    {"python", "java", "javascript", "typescript", "go", "markdown", "pdf", "openapi"},
)

_PYTHON_SHEBANG = re.compile(rb"^#!.*\bpython[23]?\b", re.IGNORECASE)
_JAVA_CLASS_MAGIC = b"\xca\xfe\xba\xbe"


@dataclass
class LanguageRegistry:
    """Maps file extensions and magic-byte signatures to programming languages."""

    _extension_map: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Register default language mappings when none are provided."""
        if not self._extension_map:
            self._register_defaults()

    def register(self, language: str, extensions: list[str]) -> None:
        """Register a language for one or more file extensions.

        Args:
            language: Canonical language name (e.g. ``python``).
            extensions: File extensions with or without a leading dot.

        """
        normalized_language = language.strip().lower()
        for extension in extensions:
            clean_ext = extension.strip().lower()
            if not clean_ext.startswith("."):
                clean_ext = f".{clean_ext}"
            self._extension_map[clean_ext] = normalized_language

    def detect(self, file_path: str, content: bytes | None = None) -> str | None:
        """Detect the programming language for a file path and optional content.

        Extension mapping is applied first. When content is provided, magic-byte
        and shebang hints can override or refine the detected language.

        Args:
            file_path: Relative or absolute path of the target file.
            content: Optional raw file bytes for shebang or compiled-class detection.

        Returns:
            Canonical language name, or ``None`` if the file is not recognized.

        """
        extension = self._extract_extension(file_path)
        language = self._extension_map.get(extension)

        if content is None:
            return language

        magic_language = self._detect_from_magic_bytes(content)
        if magic_language is not None:
            return magic_language

        return language

    def get_extension(self, file_path: str) -> str | None:
        """Return the normalized lowercase extension for a file path."""
        extension = self._extract_extension(file_path)
        return extension or None

    def is_supported_extension(self, file_path: str) -> bool:
        """Return whether the file extension is registered for detection."""
        extension = self._extract_extension(file_path)
        return extension in self._extension_map

    def supported_extensions(self) -> frozenset[str]:
        """Return all registered file extensions."""
        return frozenset(self._extension_map)

    def has_parser_extension(self, file_path: str, parser_extensions: frozenset[str]) -> bool:
        """Check whether a file path maps to a registered parser extension.

        Args:
            file_path: Relative or absolute path of the target file.
            parser_extensions: Extensions registered on a ``ParserRegistry``.

        Returns:
            True when the file extension is known to the language registry and
            has a corresponding parser registered.

        """
        extension = self._extract_extension(file_path)
        return extension in parser_extensions and extension in self._extension_map

    @staticmethod
    def _extract_extension(file_path: str) -> str:
        dot_index = file_path.rfind(".")
        if dot_index == -1:
            return ""
        return file_path[dot_index:].lower()

    @staticmethod
    def _detect_from_magic_bytes(content: bytes) -> str | None:
        if not content:
            return None

        sample = content.lstrip(b"\xef\xbb\xbf")

        if sample.startswith(_JAVA_CLASS_MAGIC):
            return "java"

        if _PYTHON_SHEBANG.match(sample):
            return "python"

        return None

    def _register_defaults(self) -> None:
        self.register("python", [".py", ".pyw", ".pyi"])
        self.register("java", [".java"])
        self.register("javascript", [".js", ".jsx", ".mjs", ".cjs"])
        self.register("typescript", [".ts", ".tsx"])
        self.register("go", [".go"])
        self.register("markdown", [".md", ".mdx"])
        self.register("pdf", [".pdf"])
