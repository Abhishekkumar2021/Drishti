"""Unit tests for GitHub URL normalization."""

from __future__ import annotations

from pathlib import Path

import pytest

from drishti.utils.github import github_cache_dir, normalize_github_url

pytestmark = pytest.mark.unit


class TestNormalizeGithubUrl:
    def test_https_url(self) -> None:
        assert (
            normalize_github_url("https://github.com/org/repo") == "https://github.com/org/repo.git"
        )

    def test_https_with_git_suffix(self) -> None:
        assert (
            normalize_github_url("https://github.com/org/repo.git")
            == "https://github.com/org/repo.git"
        )

    def test_ssh_url(self) -> None:
        assert (
            normalize_github_url("git@github.com:org/repo.git") == "https://github.com/org/repo.git"
        )

    def test_rejects_invalid(self) -> None:
        with pytest.raises(ValueError, match="Unsupported"):
            normalize_github_url("https://gitlab.com/org/repo")


class TestGithubCacheDir:
    def test_stable_under_same_url(self) -> None:
        url = "https://github.com/org/repo.git"
        a = github_cache_dir(Path("/tmp/cache"), url)
        b = github_cache_dir(Path("/tmp/cache"), url)
        assert a == b
