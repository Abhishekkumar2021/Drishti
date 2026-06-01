"""Multi-modal image analysis using Claude Vision (US-04.04).

Parses image files (.png, .jpg, .svg) and generates detailed natural
language descriptions using Claude's vision capabilities.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from drishti.api.schemas import UniversalChunk
from drishti.ingestion.base import BaseParser

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp"})
SVG_EXTENSION = ".svg"

VISION_SYSTEM_PROMPT = """\
You are an expert at analyzing technical images, diagrams, and screenshots.

Your task is to provide a detailed, structured description of the image that
can be used for semantic search and code understanding.

For architecture diagrams and flowcharts:
- Identify all components, services, and systems shown
- Describe the relationships and data flows between components
- Note any labels, annotations, or text visible in the diagram
- Identify the type of diagram (sequence, flowchart, architecture, etc.)

For code screenshots or terminal output:
- Transcribe any visible code or text (OCR)
- Identify the programming language if applicable
- Describe the purpose of the code if discernible

For UI mockups or wireframes:
- Describe the layout and components
- List interactive elements (buttons, forms, etc.)
- Note the user flow if apparent

Always:
- Be specific and technical in your descriptions
- Include any text visible in the image verbatim
- Describe spatial relationships (left, right, above, below)
- Note colors only if they convey semantic meaning"""


class ImageParser(BaseParser):
    """Parses images using Claude Vision API to generate searchable descriptions."""

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str = "claude-sonnet-4-20250514",
        enabled: bool = True,
    ) -> None:
        """Initialize the image parser.

        Args:
            api_key: Anthropic API key for Claude Vision.
            model: Claude model to use (must support vision).
            enabled: Whether vision analysis is enabled.
        """
        self._api_key = api_key
        self._model = model
        self._enabled = enabled and bool(api_key.strip())
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazily initialize the Anthropic client."""
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def parse(
        self,
        file_content: bytes,
        file_path: str,
        *,
        last_modified: datetime | None = None,
    ) -> list[UniversalChunk]:
        """Parse an image file and generate a description using Claude Vision.

        Args:
            file_content: Raw image bytes.
            file_path: Path to the image file.
            last_modified: Optional modification timestamp.

        Returns:
            List containing a single chunk with the image description.
        """
        source_id = hashlib.sha256(file_content).hexdigest()
        indexed_at = last_modified or datetime.now(UTC)
        extension = _get_extension(file_path)

        if not self._enabled:
            logger.debug("Vision analysis disabled, returning placeholder for %s", file_path)
            return [
                _build_image_chunk(
                    content=f"[Image: {file_path}] Vision analysis not enabled.",
                    file_path=file_path,
                    source_id=source_id,
                    indexed_at=indexed_at,
                    name=_extract_filename(file_path),
                )
            ]

        if extension == SVG_EXTENSION:
            return self._parse_svg(file_content, file_path, source_id, indexed_at)

        return self._parse_raster_image(file_content, file_path, source_id, indexed_at, extension)

    def _parse_raster_image(
        self,
        file_content: bytes,
        file_path: str,
        source_id: str,
        indexed_at: datetime,
        extension: str,
    ) -> list[UniversalChunk]:
        """Parse a raster image using Claude Vision."""
        media_type = _extension_to_media_type(extension)
        base64_image = base64.standard_b64encode(file_content).decode("utf-8")

        try:
            description = self._analyze_image(base64_image, media_type, file_path)
        except Exception:
            logger.exception("Vision analysis failed for %s", file_path)
            description = f"[Image: {file_path}] Vision analysis failed."

        return [
            _build_image_chunk(
                content=description,
                file_path=file_path,
                source_id=source_id,
                indexed_at=indexed_at,
                name=_extract_filename(file_path),
            )
        ]

    def _parse_svg(
        self,
        file_content: bytes,
        file_path: str,
        source_id: str,
        indexed_at: datetime,
    ) -> list[UniversalChunk]:
        """Parse an SVG file by extracting text content and optionally analyzing.

        SVGs contain readable XML/text, so we extract that directly plus
        optionally run vision analysis if it looks like a diagram.
        """
        try:
            svg_text = file_content.decode("utf-8", errors="replace")
        except Exception:
            svg_text = ""

        text_content = _extract_svg_text(svg_text)

        if self._enabled and len(file_content) < 500_000:
            try:
                base64_svg = base64.standard_b64encode(file_content).decode("utf-8")
                vision_description = self._analyze_image(
                    base64_svg,
                    "image/svg+xml",
                    file_path,
                )
                combined = f"{vision_description}\n\n## Extracted Text\n{text_content}"
                content = combined.strip()
            except Exception:
                logger.debug("SVG vision analysis failed, using text extraction only")
                content = f"[SVG Diagram: {file_path}]\n\n{text_content}"
        else:
            content = f"[SVG Diagram: {file_path}]\n\n{text_content}"

        return [
            _build_image_chunk(
                content=content,
                file_path=file_path,
                source_id=source_id,
                indexed_at=indexed_at,
                name=_extract_filename(file_path),
            )
        ]

    def _analyze_image(
        self,
        base64_image: str,
        media_type: str,
        file_path: str,
    ) -> str:
        """Call Claude Vision API to analyze the image.

        Args:
            base64_image: Base64-encoded image data.
            media_type: MIME type of the image.
            file_path: Path to the image (for context).

        Returns:
            Natural language description of the image.
        """
        client = self._get_client()

        user_prompt = (
            f"Analyze this image from the file '{file_path}'. "
            "Provide a detailed technical description suitable for semantic search."
        )

        message = client.messages.create(
            model=self._model,
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": user_prompt,
                        },
                    ],
                }
            ],
            system=VISION_SYSTEM_PROMPT,
        )

        text_blocks = [block.text for block in message.content if hasattr(block, "text")]
        return "\n".join(text_blocks).strip()


def _build_image_chunk(
    *,
    content: str,
    file_path: str,
    source_id: str,
    indexed_at: datetime,
    name: str,
) -> UniversalChunk:
    """Build a UniversalChunk for an image description."""
    return UniversalChunk(
        id=str(uuid.uuid4()),
        source_id=source_id,
        content=content,
        content_type="image_description",
        file_path=file_path,
        source_type="image",
        language=None,
        node_type="image",
        name=name,
        context_path=f"image:{file_path}",
        last_modified=indexed_at,
    )


def _get_extension(file_path: str) -> str:
    """Extract lowercase file extension."""
    dot_idx = file_path.rfind(".")
    if dot_idx == -1:
        return ""
    return file_path[dot_idx:].lower()


def _extract_filename(file_path: str) -> str:
    """Extract the filename from a path."""
    return file_path.rsplit("/", maxsplit=1)[-1]


def _extension_to_media_type(extension: str) -> str:
    """Map file extension to MIME type."""
    mapping = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    return mapping.get(extension, "image/png")


def _extract_svg_text(svg_content: str) -> str:
    """Extract visible text content from SVG XML.

    This performs a simple extraction of text elements without
    requiring a full XML parser.
    """
    import re

    text_elements = re.findall(r"<text[^>]*>([^<]+)</text>", svg_content, re.IGNORECASE)
    tspan_elements = re.findall(r"<tspan[^>]*>([^<]+)</tspan>", svg_content, re.IGNORECASE)

    all_text = text_elements + tspan_elements
    cleaned = [t.strip() for t in all_text if t.strip()]

    return "\n".join(cleaned) if cleaned else "(No text content found in SVG)"
