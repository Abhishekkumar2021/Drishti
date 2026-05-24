"""Secure filesystem path validation for ingestion."""

from __future__ import annotations

from pathlib import Path

from drishti.exceptions import PathValidationError


def resolve_repo_path(
    repo_path: str,
    *,
    allowed_roots: list[Path] | None = None,
) -> Path:
    """Resolve and validate a repository path for ingestion.

    Args:
        repo_path: User-supplied path to a local repository.
        allowed_roots: Optional list of directories paths must stay within.
            When omitted, only structural validation is applied.

    Returns:
        Resolved absolute path to the repository root.

    Raises:
        PathValidationError: If the path is missing, not a directory, escapes
            allowed roots, or contains unsafe components.

    """
    if not repo_path or not repo_path.strip():
        msg = "Repository path must not be empty"
        raise PathValidationError(msg)

    candidate = Path(repo_path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        msg = f"Repository path does not exist: {repo_path}"
        raise PathValidationError(msg) from exc
    except OSError as exc:
        msg = f"Unable to resolve repository path: {repo_path}"
        raise PathValidationError(msg) from exc

    if not resolved.is_dir():
        msg = f"Repository path is not a directory: {repo_path}"
        raise PathValidationError(msg)

    if allowed_roots and not any(resolved.is_relative_to(root.resolve()) for root in allowed_roots):
        msg = f"Repository path is outside allowed roots: {resolved}"
        raise PathValidationError(msg)

    return resolved


def is_path_within_root(path: Path, root: Path) -> bool:
    """Return whether ``path`` resolves inside ``root`` without following symlinks out."""
    root_resolved = root.resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError:
        return False

    current = path
    while current != root_resolved and current != current.parent:
        if current.is_symlink():
            link_target = current.resolve()
            try:
                link_target.relative_to(root_resolved)
            except ValueError:
                return False
        current = current.parent

    return True
