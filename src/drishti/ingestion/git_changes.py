"""Git diff resolution for incremental indexing (US-03.10)."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo
from git.diff import Diff

from drishti.exceptions import GitRepositoryError
from drishti.ingestion.walker import FileWalker


@dataclass(frozen=True)
class GitChangeSet:
    """Files to add, update, or remove between two commits."""

    head_commit: str
    base_commit: str | None
    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]

    @property
    def is_full_reindex(self) -> bool:
        """Return True when every parseable file should be indexed."""
        return self.base_commit is None


def open_repository(repo_root: Path) -> Repo:
    """Open a git repository or raise ``GitRepositoryError``."""
    try:
        return Repo(repo_root, search_parent_directories=False)
    except (InvalidGitRepositoryError, NoSuchPathError) as exc:
        msg = f"Not a git repository: {repo_root}"
        raise GitRepositoryError(msg) from exc


def resolve_head_commit(repo_root: Path) -> str:
    """Return the current HEAD commit SHA for a repository."""
    repo = open_repository(repo_root)
    if repo.head.is_detached or repo.head.commit is None:
        msg = f"Repository has no commits: {repo_root}"
        raise GitRepositoryError(msg)
    return str(repo.head.commit.hexsha)


def resolve_changes(
    repo_root: Path,
    *,
    indexed_commit: str | None,
    parseable_paths: frozenset[str] | None = None,
) -> GitChangeSet:
    """Compare indexed commit to HEAD and classify path changes."""
    repo = open_repository(repo_root)
    if repo.head.commit is None:
        msg = f"Repository has no commits: {repo_root}"
        raise GitRepositoryError(msg)

    head_commit = str(repo.head.commit.hexsha)
    if indexed_commit is None:
        paths = _discover_parseable_paths(repo_root, parseable_paths)
        return GitChangeSet(
            head_commit=head_commit,
            base_commit=None,
            added=tuple(sorted(paths)),
            modified=(),
            deleted=(),
        )

    try:
        base = repo.commit(indexed_commit)
    except Exception as exc:
        msg = f"Indexed commit not found: {indexed_commit}"
        raise GitRepositoryError(msg) from exc

    if base.hexsha == head_commit:
        return GitChangeSet(
            head_commit=head_commit,
            base_commit=indexed_commit,
            added=(),
            modified=(),
            deleted=(),
        )

    added: set[str] = set()
    modified: set[str] = set()
    deleted: set[str] = set()

    for diff_item in base.diff(repo.head.commit):
        path = _normalize_diff_path(diff_item)
        if path is None:
            continue
        if parseable_paths is not None and path not in parseable_paths:
            continue
        change = diff_item.change_type
        if change == "A":
            added.add(path)
        elif change == "M":
            modified.add(path)
        elif change == "D":
            deleted.add(path)
        elif change == "R":
            old_path = _normalize_rename_old_path(diff_item)
            if old_path is not None and (parseable_paths is None or old_path in parseable_paths):
                deleted.add(old_path)
            added.add(path)

    return GitChangeSet(
        head_commit=head_commit,
        base_commit=indexed_commit,
        added=tuple(sorted(added)),
        modified=tuple(sorted(modified)),
        deleted=tuple(sorted(deleted)),
    )


def file_content_hash(file_path: Path) -> str:
    """Return a stable SHA-256 digest for file bytes."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def _discover_parseable_paths(
    repo_root: Path,
    parseable_paths: frozenset[str] | None,
) -> set[str]:
    if parseable_paths is not None:
        return set(parseable_paths)
    walker = FileWalker(repo_root)
    return {item.relative_path for item in walker.discover() if item.has_registered_parser}


def _normalize_diff_path(diff_item: Diff) -> str | None:
    if diff_item.b_path:
        return diff_item.b_path.replace("\\", "/")
    if diff_item.a_path:
        return diff_item.a_path.replace("\\", "/")
    return None


def _normalize_rename_old_path(diff_item: Diff) -> str | None:
    if diff_item.a_path:
        return diff_item.a_path.replace("\\", "/")
    return None


def discover_parseable_files(
    repo_root: Path,
    *,
    parser_registry: object | None = None,
) -> frozenset[str]:
    """Return relative paths that have a registered parser."""
    from drishti.ingestion.base import ParserRegistry

    registry = parser_registry if isinstance(parser_registry, ParserRegistry) else None
    walker = FileWalker(repo_root, parser_registry=registry)
    paths = {item.relative_path for item in walker.discover() if item.has_registered_parser}
    return frozenset(paths)


def filter_existing_paths(repo_root: Path, paths: Iterable[str]) -> tuple[str, ...]:
    """Keep only paths that still exist on disk."""
    existing: list[str] = []
    for path in paths:
        if (repo_root / path).is_file():
            existing.append(path)
    return tuple(existing)
