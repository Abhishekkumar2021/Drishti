"""Unit tests for gitignore pattern matching."""

from __future__ import annotations

from pathlib import Path

import pytest

from drishti.ingestion.gitignore import GitignoreMatcher

pytestmark = pytest.mark.unit


@pytest.fixture
def repo_with_gitignore(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitignore").write_text("*.log\nbuild/\n", encoding="utf-8")
    return repo


class TestGitignoreMatcher:
    def test_ignores_matching_files(self, repo_with_gitignore: Path) -> None:
        matcher = GitignoreMatcher(repo_with_gitignore)

        assert matcher.is_ignored("tmp/debug.log")
        assert not matcher.is_ignored("src/main.py")

    def test_ignores_matching_directories(self, repo_with_gitignore: Path) -> None:
        matcher = GitignoreMatcher(repo_with_gitignore)

        assert matcher.is_ignored("build", is_dir=True)
        assert matcher.is_ignored("build/output", is_dir=True)

    def test_always_ignores_git_directory(self, repo_with_gitignore: Path) -> None:
        matcher = GitignoreMatcher(repo_with_gitignore)

        assert matcher.is_ignored(".git", is_dir=True)
        assert matcher.is_ignored(".git/config")

    def test_supports_negated_patterns(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".gitignore").write_text("*.log\n!important.log\n", encoding="utf-8")

        matcher = GitignoreMatcher(repo)

        assert matcher.is_ignored("debug.log")
        assert not matcher.is_ignored("important.log")
