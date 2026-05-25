"""Unit tests for OpenAPI document ingestion (US-04.05)."""

from __future__ import annotations

from pathlib import Path

import pytest

from drishti.ingestion.documents.openapi import OpenApiParser

pytestmark = pytest.mark.unit

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "openapi.yaml"


class TestOpenApiParser:
    def test_parses_endpoints_from_yaml_fixture(self) -> None:
        content = _FIXTURE.read_bytes()
        parser = OpenApiParser()
        chunks = parser.parse(content, "openapi.yaml")
        assert len(chunks) == 2
        methods = {chunk.context_path for chunk in chunks}
        assert "GET /users" in methods
        assert "POST /users" in methods
        post = next(chunk for chunk in chunks if chunk.context_path == "POST /users")
        assert post.content_type == "api_endpoint"
        assert "Request body" in post.content
        assert post.source_type == "openapi"

    def test_ignores_non_openapi_yaml_files(self) -> None:
        parser = OpenApiParser()
        text = b"title: Not an API\nitems:\n  - one\n"
        assert parser.parse(text, "docker-compose.yaml") == []

    def test_ignores_wrong_filename(self) -> None:
        parser = OpenApiParser()
        spec = b'{"openapi":"3.0.0","paths":{}}'
        assert parser.parse(spec, "package.json") == []
