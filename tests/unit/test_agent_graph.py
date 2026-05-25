"""Unit tests for the LangGraph agent."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from drishti.agent.runner import AgentRunner
from drishti.config import Settings
from drishti.generation.models import ContextChunk
from drishti.generation.streaming import format_sse_event


@pytest.mark.unit
def test_agent_ask_via_graph() -> None:
    rag = MagicMock()
    rag.settings = Settings(agent_max_retrieval_loops=1)
    rag.llm = MagicMock()
    rag.llm.complete.return_value = "Auth is in [src/auth.py:L1-5]."
    rag.prepare_context.return_value = (
        (
            ContextChunk(
                chunk_id="c1",
                file_path="src/auth.py",
                content="code",
                start_line=1,
                end_line=5,
            ),
        ),
        "user prompt",
    )
    rag.extract_citations.return_value = []

    runner = AgentRunner(rag, rag.settings)
    result = runner.ask("where is auth?")
    assert "Auth is in" in result.answer
    rag.prepare_context.assert_called()


@pytest.mark.unit
def test_agent_stream_emits_sse_events() -> None:
    rag = MagicMock()
    rag.settings = Settings(agent_max_retrieval_loops=1)
    rag.llm = MagicMock()
    rag.llm.stream.return_value = iter(["Hi "])
    chunk = ContextChunk(
        chunk_id="c1",
        file_path="src/a.py",
        content="code",
        start_line=1,
        end_line=2,
    )
    rag.prepare_context.return_value = ((chunk,), "prompt")
    rag.extract_citations.return_value = []

    runner = AgentRunner(rag, rag.settings)
    events = list(runner.ask_stream("question"))
    formatted = [format_sse_event(event) for event in events]

    assert any("event: context" in line for line in formatted)
    assert any("event: token" in line for line in formatted)
    assert any("event: done" in line for line in formatted)
