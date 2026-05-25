"""Clone or update remote Git repositories for ingestion."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from git import Repo

from drishti.exceptions import GitRepositoryError

_GITHUB_HTTPS = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?(?:#.*)?$",
    re.IGNORECASE,
)
_GITHUB_SSH = re.compile(
    r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
    re.IGNORECASE,
)


def normalize_github_url(url: str) -> str:
    """Return a canonical HTTPS clone URL for supported GitHub remote forms."""
    raw = url.strip()
    if not raw:
        msg = "Repository URL is required"
        raise ValueError(msg)

    ssh = _GITHUB_SSH.match(raw)
    if ssh:
        owner = ssh.group("owner")
        repo = ssh.group("repo").removesuffix(".git")
        return f"https://github.com/{owner}/{repo}.git"

    https = _GITHUB_HTTPS.match(raw)
    if https:
        owner = https.group("owner")
        repo = https.group("repo").removesuffix(".git")
        return f"https://github.com/{owner}/{repo}.git"

    msg = (
        "Unsupported repository URL. Use https://github.com/owner/repo "
        "or git@github.com:owner/repo.git"
    )
    raise ValueError(msg)


def github_cache_dir(cache_root: Path, clone_url: str) -> Path:
    """Return stable on-disk path for a cached GitHub clone."""
    digest = hashlib.sha256(clone_url.encode("utf-8")).hexdigest()[:16]
    slug = clone_url.rstrip("/").split("/")[-1].removesuffix(".git")
    return cache_root / f"{slug}-{digest}"


def clone_or_pull_github_repo(
    url: str,
    *,
    cache_root: Path | None = None,
    branch: str | None = "main",
) -> Path:
    """Clone or pull a GitHub repository and return the local path."""
    clone_url = normalize_github_url(url)
    root = cache_root or Path.home() / ".cache" / "drishti" / "repos"
    root.mkdir(parents=True, exist_ok=True)
    target = github_cache_dir(root, clone_url)

    try:
        if target.exists() and (target / ".git").is_dir():
            repo = Repo(target)
            origin = repo.remotes.origin
            origin.fetch(depth=1)
            if branch:
                repo.git.checkout(branch)
            origin.pull()
            return target.resolve()

        if target.exists():
            import shutil

            shutil.rmtree(target)

        if branch:
            Repo.clone_from(clone_url, str(target), branch=branch, depth=1)
        else:
            Repo.clone_from(clone_url, str(target), depth=1)
        return target.resolve()
    except Exception as exc:
        msg = f"Failed to clone repository: {exc}"
        raise GitRepositoryError(msg) from exc
