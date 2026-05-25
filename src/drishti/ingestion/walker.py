"""Repository file discovery for the ingestion pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from drishti.ingestion.content_router import ContentRouter
from drishti.ingestion.gitignore import GitignoreMatcher
from drishti.utils.language import LanguageRegistry
from drishti.utils.paths import is_path_within_root

if TYPE_CHECKING:
    from collections.abc import Iterator

    from drishti.ingestion.base import ParserRegistry

logger = logging.getLogger(__name__)

_MAGIC_BYTES_LIMIT = 512


@dataclass(frozen=True)
class DiscoveredFile:
    """A code file discovered during a repository walk."""

    relative_path: str
    absolute_path: Path
    language: str | None
    extension: str
    has_registered_parser: bool
    content_kind: str | None = None
    detection_method: str | None = None


class FileWalker:
    """Recursively scans a repository and detects supported code files."""

    def __init__(
        self,
        root: Path,
        *,
        language_registry: LanguageRegistry | None = None,
        parser_registry: ParserRegistry | None = None,
        recursive: bool = True,
        inspect_magic_bytes: bool = True,
        follow_symlinks: bool = False,
    ) -> None:
        """Initialize a walker for a repository root.

        Args:
            root: Absolute or relative path to the repository root.
            language_registry: Registry used to map files to languages.
            parser_registry: Optional parser registry for routing validation.
            recursive: Whether to walk nested directories.
            inspect_magic_bytes: Whether to read file headers for shebang detection.
            follow_symlinks: Whether to follow symbolic links (default: skip).

        """
        self.root = root.resolve()
        self.language_registry = language_registry or LanguageRegistry()
        self.parser_registry = parser_registry
        self.recursive = recursive
        self.inspect_magic_bytes = inspect_magic_bytes
        self.follow_symlinks = follow_symlinks
        self._gitignore = GitignoreMatcher(self.root)
        parser_extensions = (
            parser_registry.registered_extensions()
            if parser_registry is not None
            else frozenset()
        )
        self._content_router = ContentRouter(
            extension_map=self.language_registry.extension_map,
            parser_extensions=parser_extensions,
        )

    def walk(self) -> Iterator[DiscoveredFile]:
        """Yield discovered code files under the repository root."""
        yield from self._walk_directory(self.root, base_prefix=Path())

    def discover(self) -> list[DiscoveredFile]:
        """Return all discovered code files as a list."""
        return list(self.walk())

    def _walk_directory(self, directory: Path, *, base_prefix: Path) -> Iterator[DiscoveredFile]:
        if not self.recursive and base_prefix != Path():
            return

        try:
            entries = sorted(directory.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            logger.warning("Skipping unreadable directory %s: %s", directory, exc)
            return

        for entry in entries:
            if entry.is_symlink() and not self.follow_symlinks:
                continue

            relative_path = (base_prefix / entry.name).as_posix()
            resolved_entry = entry.resolve()

            if not is_path_within_root(resolved_entry, self.root):
                logger.warning("Skipping path outside repository root: %s", relative_path)
                continue

            if entry.is_dir():
                if self._gitignore.is_ignored(relative_path, is_dir=True):
                    continue
                if self.recursive:
                    yield from self._walk_directory(
                        resolved_entry,
                        base_prefix=base_prefix / entry.name,
                    )
                continue

            if not entry.is_file():
                continue

            if self._gitignore.is_ignored(relative_path, is_dir=False):
                continue

            content = self._read_magic_bytes(resolved_entry) if self.inspect_magic_bytes else None
            classification = self._content_router.classify(relative_path, content)
            if classification.kind == "unknown":
                continue

            has_registered_parser = self._content_router.has_parser(classification)

            yield DiscoveredFile(
                relative_path=relative_path,
                absolute_path=resolved_entry,
                language=classification.language,
                extension=classification.effective_extension,
                has_registered_parser=has_registered_parser,
                content_kind=classification.kind,
                detection_method=classification.detection_method,
            )

    def _read_magic_bytes(self, file_path: Path) -> bytes | None:
        try:
            with file_path.open("rb") as handle:
                return handle.read(_MAGIC_BYTES_LIMIT)
        except OSError as exc:
            logger.warning("Unable to read file %s: %s", file_path, exc)
            return None
