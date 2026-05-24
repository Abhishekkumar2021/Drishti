"""Unit tests for RAG pipeline orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from drishti.config import Settings
from drishti.generation.context import ContextBuilder
from drishti.generation.llm import MockChatLLM
from drishti.generation.pipeline import RAGPipeline
from drishti.generation.streaming import format_sse_event
from drishti.search.models import SearchHit

pytestmark = pytest.mark.unit


class TestRAGPipeline:
    def test_ask_returns_answer_with_valid_citation(self) -> None:
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
            llm=MockChatLLM(response="Auth is in [src/auth.py:L1-5]."),
            context_builder=ContextBuilder(),
            settings=settings,
        )

        answer = pipeline.ask("Where is auth?")

        assert "Auth is in" in answer.answer
        assert len(answer.citations) == 1
        assert answer.citations[0].valid is True

    def test_ask_stream_emits_sse_events(self) -> None:
        search = MagicMock()
        search.search.return_value = [
            SearchHit(
                chunk_id="c1",
                score=0.9,
                content="code",
                payload={"file_path": "src/a.py", "start_line": 1, "end_line": 2},
                source="rerank",
            )
        ]
        settings = Settings()
        pipeline = RAGPipeline(
            search=search,
            llm=MockChatLLM(response="Hi [src/a.py:L1-2]"),
            context_builder=ContextBuilder(),
            settings=settings,
        )

        events = list(pipeline.ask_stream("question"))
        formatted = [format_sse_event(event) for event in events]

        assert any(line.startswith("event: context") for line in formatted)
        assert any("event: token" in line for line in formatted)
        assert any("event: done" in line for line in formatted)
