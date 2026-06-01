"""Unit tests for the image parser (US-04.04)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from drishti.ingestion.documents.image import (
    IMAGE_EXTENSIONS,
    ImageParser,
    _build_image_chunk,
    _extension_to_media_type,
    _extract_filename,
    _extract_svg_text,
    _get_extension,
)


class TestImageParserHelpers:
    """Test helper functions for image parsing."""

    def test_get_extension(self) -> None:
        """_get_extension should extract lowercase extension."""
        assert _get_extension("path/to/image.PNG") == ".png"
        assert _get_extension("photo.JPEG") == ".jpeg"
        assert _get_extension("no_extension") == ""

    def test_extract_filename(self) -> None:
        """_extract_filename should get the filename from path."""
        assert _extract_filename("path/to/diagram.png") == "diagram.png"
        assert _extract_filename("simple.jpg") == "simple.jpg"

    def test_extension_to_media_type(self) -> None:
        """_extension_to_media_type should map extensions to MIME types."""
        assert _extension_to_media_type(".png") == "image/png"
        assert _extension_to_media_type(".jpg") == "image/jpeg"
        assert _extension_to_media_type(".jpeg") == "image/jpeg"
        assert _extension_to_media_type(".gif") == "image/gif"
        assert _extension_to_media_type(".webp") == "image/webp"
        assert _extension_to_media_type(".svg") == "image/svg+xml"
        assert _extension_to_media_type(".unknown") == "image/png"

    def test_extract_svg_text(self) -> None:
        """_extract_svg_text should extract text from SVG elements."""
        svg = """
        <svg>
            <text>Hello World</text>
            <tspan>Label 1</tspan>
            <tspan>Label 2</tspan>
        </svg>
        """
        result = _extract_svg_text(svg)
        assert "Hello World" in result
        assert "Label 1" in result
        assert "Label 2" in result

    def test_extract_svg_text_no_text(self) -> None:
        """_extract_svg_text should handle SVGs with no text."""
        svg = "<svg><rect width='100' height='100'/></svg>"
        result = _extract_svg_text(svg)
        assert "(No text content found in SVG)" in result


class TestImageParserDisabled:
    """Test ImageParser when vision is disabled."""

    def test_parse_returns_placeholder_when_disabled(self) -> None:
        """Parser should return placeholder chunk when disabled."""
        parser = ImageParser(api_key="", enabled=False)

        fake_png = b"\x89PNG\r\n\x1a\n" + b"fake image data"
        chunks = parser.parse(fake_png, "docs/diagram.png")

        assert len(chunks) == 1
        assert "Vision analysis not enabled" in chunks[0].content
        assert chunks[0].content_type == "image_description"
        assert chunks[0].file_path == "docs/diagram.png"


class TestImageParserEnabled:
    """Test ImageParser with mocked Claude Vision API."""

    def test_parse_raster_image_calls_anthropic(self) -> None:
        """Parser should call Anthropic API for raster images."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_block = MagicMock()
        mock_block.text = "This is an architecture diagram showing..."
        mock_message.content = [mock_block]
        mock_client.messages.create.return_value = mock_message

        parser = ImageParser(api_key="test-key", enabled=True)
        parser._client = mock_client

        fake_png = b"\x89PNG\r\n\x1a\n" + b"fake image data"
        chunks = parser.parse(fake_png, "docs/arch.png")

        assert len(chunks) == 1
        assert "architecture diagram" in chunks[0].content
        assert chunks[0].content_type == "image_description"
        mock_client.messages.create.assert_called_once()

    def test_parse_handles_api_failure(self) -> None:
        """Parser should handle API failures gracefully."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")

        parser = ImageParser(api_key="test-key", enabled=True)
        parser._client = mock_client

        fake_png = b"\x89PNG\r\n\x1a\n" + b"fake image data"
        chunks = parser.parse(fake_png, "docs/arch.png")

        assert len(chunks) == 1
        assert "Vision analysis failed" in chunks[0].content


class TestBuildImageChunk:
    """Test chunk building function."""

    def test_build_image_chunk(self) -> None:
        """_build_image_chunk should create valid UniversalChunk."""
        chunk = _build_image_chunk(
            content="A flowchart showing user authentication",
            file_path="docs/auth-flow.png",
            source_id="abc123",
            indexed_at=datetime(2026, 1, 1, tzinfo=UTC),
            name="auth-flow.png",
        )

        assert chunk.content == "A flowchart showing user authentication"
        assert chunk.content_type == "image_description"
        assert chunk.source_type == "image"
        assert chunk.file_path == "docs/auth-flow.png"
        assert chunk.name == "auth-flow.png"
        assert chunk.node_type == "image"
        assert "image:" in chunk.context_path


class TestImageExtensions:
    """Test supported image extensions."""

    def test_supported_extensions(self) -> None:
        """IMAGE_EXTENSIONS should include common image formats."""
        assert ".png" in IMAGE_EXTENSIONS
        assert ".jpg" in IMAGE_EXTENSIONS
        assert ".jpeg" in IMAGE_EXTENSIONS
        assert ".gif" in IMAGE_EXTENSIONS
        assert ".webp" in IMAGE_EXTENSIONS
