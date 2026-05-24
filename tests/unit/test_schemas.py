"""Unit tests for API schemas."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from drishti.api.schemas import AskRequest, ChatMessage, IngestionRequest

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
