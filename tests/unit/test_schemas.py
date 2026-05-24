"""Unit tests for API schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from drishti.api.schemas import AskRequest, ChatMessage, IngestionRequest, UniversalChunk

pytestmark = pytest.mark.unit


class TestIngestionRequest:
    def test_resolves_valid_repo_path(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        request = IngestionRequest(repo_path=str(repo))
        assert request.resolved_repo_path() == repo.resolve()

    def test_rejects_empty_repo_path(self) -> None:
        with pytest.raises(ValidationError):
            IngestionRequest(repo_path="")


class TestUniversalChunk:
    def test_rejects_end_line_before_start_line(self) -> None:
        with pytest.raises(ValidationError, match="end_line must be greater than or equal"):
            UniversalChunk(
                id="id",
                source_id="src",
                content="x",
                content_type="code",
                file_path="a.py",
                source_type="git_repo",
                start_line=10,
                end_line=5,
                last_modified=datetime.now(UTC),
            )


class TestAskRequest:
    def test_requires_non_empty_question(self) -> None:
        with pytest.raises(ValidationError):
            AskRequest(question="")

    def test_accepts_structured_history(self) -> None:
        request = AskRequest(
            question="How does auth work?",
            conversation_history=[
                ChatMessage(role="user", content="Hello"),
                ChatMessage(role="assistant", content="Hi"),
            ],
        )
        assert len(request.conversation_history) == 2
