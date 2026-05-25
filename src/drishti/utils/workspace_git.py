"""Initialize or update git snapshots for non-clone workspace roots."""

from __future__ import annotations

import logging
from pathlib import Path

from git import Repo

from drishti.exceptions import GitRepositoryError

logger = logging.getLogger(__name__)


def ensure_git_snapshot(root: Path, *, commit_message: str = "Drishti workspace snapshot") -> str:
    """Ensure ``root`` is a git repo and commit all current files.

    Upload and artifact directories are indexed via the existing incremental
    git pipeline. New uploads trigger a fresh commit so diffs are detected.
    """
    root = root.resolve()
    if not root.is_dir():
        msg = f"Workspace root is not a directory: {root}"
        raise GitRepositoryError(msg)

    if (root / ".git").is_dir():
        repo = Repo(root)
    else:
        repo = Repo.init(root)
        with (root / ".gitignore").open("a", encoding="utf-8") as handle:
            handle.write("\n# Drishti workspace metadata\n.drishti/\n")

    repo.git.add(all=True)
    if repo.is_dirty(untracked_files=True) or not repo.head.is_valid():
        repo.index.commit(commit_message)
    elif repo.head.commit is None:
        msg = f"Workspace repository has no commits: {root}"
        raise GitRepositoryError(msg)

    return str(repo.head.commit.hexsha)
