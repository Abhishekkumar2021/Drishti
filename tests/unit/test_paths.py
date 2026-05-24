"""Unit tests for secure path validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from drishti.exceptions import PathValidationError
from drishti.utils.paths import is_path_within_root, resolve_repo_path

pytestmark = pytest.mark.unit


class TestResolveRepoPath:
    def test_resolves_existing_directory(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        resolved = resolve_repo_path(str(repo))
        assert resolved == repo.resolve()

    def test_rejects_missing_path(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing"
        with pytest.raises(PathValidationError):
            resolve_repo_path(str(missing))

    def test_enforces_allowed_roots(self, tmp_path: Path) -> None:
        allowed = tmp_path / "allowed"
        outside = tmp_path / "outside"
        allowed.mkdir()
        outside.mkdir()
        with pytest.raises(PathValidationError):
            resolve_repo_path(str(outside), allowed_roots=[allowed])


class TestIsPathWithinRoot:
    def test_rejects_symlink_escaping_root(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        outside = tmp_path / "outside"
        root.mkdir()
        outside.mkdir()
        (outside / "secret.py").write_text("secret\n", encoding="utf-8")
        link = root / "escape"
        link.symlink_to(outside / "secret.py", target_is_directory=False)
        assert is_path_within_root(link, root) is False
