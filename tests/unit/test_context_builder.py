"""Unit tests for RAG context builder (US-07.01)."""

from __future__ import annotations

import pytest

from drishti.generation.context import ContextBuilder
from drishti.search.models import SearchHit

pytestmark = pytest.mark.unit


def _hit(**payload: object) -> SearchHit:
    base = {
        "file_path": "src/auth.py",
        "start_line": 10,
        "end_line": 20,
        "language": "python",
        "name": "validate",
    }
    base.update(payload)
    return SearchHit(
        chunk_id="c1",
        score=0.9,
        content="def validate():\n    return True\n",
        payload=base,
        source="rerank",
    )


class TestContextBuilder:
    def test_renders_xml_delimiters(self) -> None:
        builder = ContextBuilder(max_chars=10_000, max_chunks=5)
        chunks = builder.build_from_hits([_hit()])
        xml = builder.render_xml(chunks)
        assert '<context id="1"' in xml
        assert 'file="src/auth.py"' in xml
        assert 'start="10"' in xml
        assert "def validate" in xml

    def test_respects_max_chars_budget(self) -> None:
        builder = ContextBuilder(max_chars=80, max_chunks=10)
        hits = [_hit(content="x" * 50), _hit(content="y" * 50)]
        chunks = builder.build_from_hits(hits)
        assert len(chunks) == 1
