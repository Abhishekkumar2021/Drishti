"""Content-aware file classification beyond naive extension matching."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

from drishti.ingestion.documents.paths import is_openapi_spec_path

ContentKind = Literal["code", "markdown", "pdf", "openapi", "unknown"]
DetectionMethod = Literal["extension", "magic_bytes", "content_sniff", "path_heuristic"]

_PDF_MAGIC = b"%PDF-"
_OPENAPI_MARKERS = (b"openapi:", b"swagger:", b'"openapi"', b'"swagger"')
_MARKDOWN_HINT = re.compile(
    r"^(\s*#{1,6}\s+\S|```|\*\*[^*]+\*\*|\[.+\]\(.+\))",
    re.MULTILINE,
)
_README_NAMES = frozenset(
    {"readme", "readme.md", "readme.markdown", "contributing", "contributing.md"},
)


@dataclass(frozen=True)
class FileClassification:
    """Result of intelligent routing for a single file."""

    kind: ContentKind
    language: str | None
    effective_extension: str
    detection_method: DetectionMethod
    confidence: float


class ContentRouter:
    """Classify files using extension, path heuristics, and content sniffing."""

    def __init__(
        self,
        *,
        extension_map: dict[str, str],
        parser_extensions: frozenset[str],
    ) -> None:
        self._extension_map = extension_map
        self._parser_extensions = parser_extensions

    def classify(self, file_path: str, content: bytes | None = None) -> FileClassification:
        """Return how a file should be parsed and indexed."""
        extension = _extract_extension(file_path)
        path_language = self._extension_map.get(extension)

        if content:
            magic = _classify_magic(content)
            if magic is not None:
                return magic

            sniffed = _classify_text_content(file_path, content, extension)
            if sniffed is not None:
                return sniffed

        if is_openapi_spec_path(file_path) and extension in {".yaml", ".yml", ".json"}:
            return FileClassification(
                kind="openapi",
                language="openapi",
                effective_extension=extension,
                detection_method="path_heuristic",
                confidence=0.9,
            )

        basename = file_path.rsplit("/", maxsplit=1)[-1].lower()
        if basename in _README_NAMES or basename.startswith("readme."):
            if ".md" in self._parser_extensions:
                return FileClassification(
                    kind="markdown",
                    language="markdown",
                    effective_extension=".md",
                    detection_method="path_heuristic",
                    confidence=0.85,
                )

        if path_language and extension in self._parser_extensions:
            kind: ContentKind = "code"
            if path_language in {"markdown", "pdf", "openapi"}:
                kind = path_language  # type: ignore[assignment]
            return FileClassification(
                kind=kind,
                language=path_language,
                effective_extension=extension,
                detection_method="extension",
                confidence=0.75,
            )

        return FileClassification(
            kind="unknown",
            language=None,
            effective_extension=extension,
            detection_method="extension",
            confidence=0.0,
        )

    def has_parser(self, classification: FileClassification) -> bool:
        """Return whether a registered parser exists for this classification."""
        if classification.kind == "unknown":
            return False
        return classification.effective_extension in self._parser_extensions


def _extract_extension(file_path: str) -> str:
    dot_index = file_path.rfind(".")
    if dot_index == -1:
        return ""
    return file_path[dot_index:].lower()


def _classify_magic(content: bytes) -> FileClassification | None:
    sample = content.lstrip(b"\xef\xbb\xbf")[:512]
    if sample.startswith(_PDF_MAGIC):
        return FileClassification(
            kind="pdf",
            language=None,
            effective_extension=".pdf",
            detection_method="magic_bytes",
            confidence=0.99,
        )
    if sample.startswith(b"\xca\xfe\xba\xbe"):
        return FileClassification(
            kind="code",
            language="java",
            effective_extension=".java",
            detection_method="magic_bytes",
            confidence=0.95,
        )
    if sample.startswith(b"#!") and b"python" in sample[:80].lower():
        return FileClassification(
            kind="code",
            language="python",
            effective_extension=".py",
            detection_method="magic_bytes",
            confidence=0.95,
        )
    return None


def _classify_text_content(
    file_path: str,
    content: bytes,
    extension: str,
) -> FileClassification | None:
    text = content.decode("utf-8", errors="ignore").strip()
    if not text:
        return None

    lowered = text.lower()
    if any(marker.decode("utf-8", errors="ignore") in lowered[:2000] for marker in _OPENAPI_MARKERS):
        if extension in {".yaml", ".yml", ".json", ""} or is_openapi_spec_path(file_path):
            ext = extension or (".json" if text.startswith("{") else ".yaml")
            return FileClassification(
                kind="openapi",
                language="openapi",
                effective_extension=ext,
                detection_method="content_sniff",
                confidence=0.92,
            )

    if extension == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and ("openapi" in payload or "swagger" in payload):
            return FileClassification(
                kind="openapi",
                language="openapi",
                effective_extension=".json",
                detection_method="content_sniff",
                confidence=0.95,
            )

    if extension in {".md", ".mdx", ""} and _MARKDOWN_HINT.search(text[:4000]):
        ext = extension if extension in {".md", ".mdx"} else ".md"
        return FileClassification(
            kind="markdown",
            language="markdown",
            effective_extension=ext,
            detection_method="content_sniff",
            confidence=0.8,
        )

    return None
