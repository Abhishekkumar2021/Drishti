"""Unit tests for RAG context preparation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from drishti.config import Settings
from drishti.generation.context import ContextBuilder
from drishti.generation.llm import MockChatLLM
from drishti.generation.models import ContextChunk
from drishti.generation.pipeline import RAGPipeline
from drishti.search.models import SearchHit

pytestmark = pytest.mark.unit


class TestRAGPipeline:
    def test_prepare_context_builds_prompt_from_hits(self) -> None:
        search = MagicMock()
        search.search.return_value = [
            SearchHit(
                chunk_id="c1",
                score=0.9,
                content="def validate(): pass",
                payload={
                    "file_path": "src/auth.py",
                    "start_line": 1,
                    "end_line": 5,
                },
                source="rerank",
            )
        ]
        settings = Settings()
        pipeline = RAGPipeline(
            search=search,
            llm=MockChatLLM(response="unused"),
            context_builder=ContextBuilder(),
            settings=settings,
        )

        chunks, prompt = pipeline.prepare_context(
            "Where is auth?",
            filters=None,
            conversation_history=None,
        )

        assert len(chunks) == 1
        assert "Where is auth?" in prompt
        assert "src/auth.py" in prompt

    def test_extract_citations_validates_against_chunks(self) -> None:
        search = MagicMock()
        settings = Settings()
        pipeline = RAGPipeline(
            search=search,
            llm=MockChatLLM(response="unused"),
            context_builder=ContextBuilder(),
            settings=settings,
        )
        chunk = ContextChunk(
            chunk_id="c1",
            file_path="src/auth.py",
            content="code",
            start_line=1,
            end_line=5,
        )
        citations = pipeline.extract_citations("See [src/auth.py:L1-5].", (chunk,))
        assert len(citations) == 1
        assert citations[0].valid is True
