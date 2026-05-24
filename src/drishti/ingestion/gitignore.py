"""Minimal gitignore pattern matching for repository file walks."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitignoreMatcher:
    """Evaluates gitignore-style patterns against repository-relative paths."""

    root: Path
    _rules: list[tuple[str, bool, bool]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Load gitignore rules and always exclude the .git directory."""
        self.root = self.root.resolve()
        self._rules.append(("**/.git/**", False, False))
        self._rules.append(("**/.git", False, False))
        self._load_gitignore_files()

    def is_ignored(self, relative_path: str, *, is_dir: bool = False) -> bool:
        """Return whether a path should be excluded from ingestion.

        Args:
            relative_path: Path relative to the repository root using POSIX separators.
            is_dir: Whether the path refers to a directory.

        Returns:
            True when the path matches an active ignore rule.

        """
        normalized = relative_path.replace("\\", "/").strip("/")
        if not normalized:
            return False

        ignored = False
        for pattern, negated, dir_only in self._rules:
            matched = self._rule_matches(pattern, normalized, is_dir=is_dir, dir_only=dir_only)
            if matched:
                ignored = not negated

        return ignored

    @staticmethod
    def _rule_matches(pattern: str, relative_path: str, *, is_dir: bool, dir_only: bool) -> bool:
        if pattern in {"**/.git", "**/.git/**"}:
            return GitignoreMatcher._matches_git_pattern(pattern, relative_path)

        if dir_only:
            return GitignoreMatcher._matches_directory_pattern(pattern, relative_path)

        if is_dir:
            return False

        return GitignoreMatcher._matches_glob(pattern, relative_path)

    @staticmethod
    def _matches_git_pattern(pattern: str, relative_path: str) -> bool:
        if pattern == "**/.git":
            return (
                relative_path == ".git"
                or relative_path.startswith(".git/")
                or "/.git/" in f"/{relative_path}/"
                or relative_path.endswith("/.git")
            )

        return relative_path.startswith(".git/") or "/.git/" in f"/{relative_path}/"

    @staticmethod
    def _matches_directory_pattern(pattern: str, relative_path: str) -> bool:
        if relative_path == pattern or relative_path.startswith(f"{pattern}/"):
            return True
        return f"/{pattern}/" in f"/{relative_path}/" or relative_path.endswith(f"/{pattern}")

    @staticmethod
    def _matches_glob(pattern: str, relative_path: str) -> bool:
        if fnmatch.fnmatchcase(relative_path, pattern):
            return True

        basename = relative_path.rsplit("/", 1)[-1]
        return fnmatch.fnmatch(basename, pattern)

    def _load_gitignore_files(self) -> None:
        for gitignore_path in sorted(self.root.rglob(".gitignore")):
            if self._is_under_git_dir(gitignore_path):
                continue

            base_dir = gitignore_path.parent.relative_to(self.root)
            for raw_line in gitignore_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                negated = line.startswith("!")
                if negated:
                    line = line[1:].strip()
                    if not line:
                        continue

                dir_only = line.endswith("/")
                if dir_only:
                    line = line.rstrip("/")

                pattern = self._normalize_pattern(line, base_dir)
                self._rules.append((pattern, negated, dir_only))

    def _normalize_pattern(self, pattern: str, base_dir: Path) -> str:
        anchored = pattern.startswith("/")
        if anchored:
            pattern = pattern.lstrip("/")

        if base_dir != Path("."):
            prefix = base_dir.as_posix()
            if anchored:
                pattern = f"{prefix}/{pattern}"
            elif "/" not in pattern:
                pattern = f"{prefix}/**/{pattern}"
            else:
                pattern = f"{prefix}/{pattern}"

        return pattern.replace("\\", "/")

    @staticmethod
    def _is_under_git_dir(path: Path) -> bool:
        return any(part == ".git" for part in path.parts)
