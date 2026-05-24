from abc import ABC, abstractmethod
from datetime import datetime

from drishti.api.schemas import UniversalChunk


class BaseParser(ABC):
    """Abstract base class defining the parsing strategy contract.

    All file parsers (AST, PDF, Markdown) must implement this interface.
    """

    @abstractmethod
    def parse(
        self,
        file_content: bytes,
        file_path: str,
        *,
        last_modified: datetime | None = None,
    ) -> list[UniversalChunk]:
        """Parse raw file bytes into structured universal chunks.

        Args:
            file_content: Raw binary contents of the target file.
            file_path: Relative path of the file within the workspace.
            last_modified: Optional file modification time for chunk metadata.

        Returns:
            List of structured universal chunk objects.

        """
        raise NotImplementedError


class ParserRegistry:
    """Registry that maps file extensions to parser strategy instances."""

    def __init__(self) -> None:
        """Initialize an empty parser registry."""
        self._parsers: dict[str, BaseParser] = {}

    def register(self, extension: str, parser: BaseParser) -> None:
        """Register a parser strategy for a file extension.

        Args:
            extension: File extension suffix (e.g. ``.py``, ``.pdf``).
            parser: Concrete parser strategy instance.

        """
        clean_ext = extension.strip().lower()
        if not clean_ext.startswith("."):
            clean_ext = f".{clean_ext}"
        self._parsers[clean_ext] = parser

    def get_parser(self, file_path: str) -> BaseParser:
        """Return the parser strategy registered for a file path.

        Args:
            file_path: Relative or absolute path of the file to parse.

        Returns:
            Parser strategy instance matching the file extension.

        Raises:
            ValueError: If no parser is registered for the extension.

        """
        dot_index = file_path.rfind(".")
        if dot_index == -1:
            msg = f"Could not resolve file extension for path: {file_path}"
            raise ValueError(msg)

        ext = file_path[dot_index:].lower()
        if ext not in self._parsers:
            msg = f"No parser strategy registered for file extension: {ext}"
            raise ValueError(msg)

        return self._parsers[ext]

    def registered_extensions(self) -> frozenset[str]:
        """Return all file extensions with registered parsers."""
        return frozenset(self._parsers)
