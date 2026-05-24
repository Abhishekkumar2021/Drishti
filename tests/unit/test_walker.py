"""Unit tests for repository file walking."""

from __future__ import annotations

from pathlib import Path

import pytest

from drishti.api.schemas import UniversalChunk
from drishti.ingestion.base import BaseParser, ParserRegistry
from drishti.ingestion.walker import FileWalker

pytestmark = pytest.mark.unit


class StubParser(BaseParser):
    def parse(self, file_content: bytes, file_path: str) -> list[UniversalChunk]:
        return []


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / "src" / "App.tsx").write_text("export const App = () => null;\n", encoding="utf-8")
    (repo / "build").mkdir()
    (repo / "build" / "ignored.log").write_text("noise\n", encoding="utf-8")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "package.js").write_text("module.exports = {};\n", encoding="utf-8")
    (repo / ".gitignore").write_text(
        "\n".join(
            [
                "*.log",
                "node_modules/",
            ]
        ),
        encoding="utf-8",
    )
    return repo


class TestFileWalker:
    def test_discovers_supported_code_files(self, sample_repo: Path) -> None:
        walker = FileWalker(sample_repo)
        discovered = {item.relative_path: item.language for item in walker.discover()}

        assert discovered == {
            "src/main.py": "python",
            "src/App.tsx": "typescript",
        }

    def test_respects_gitignore_patterns(self, sample_repo: Path) -> None:
        walker = FileWalker(sample_repo)
        paths = {item.relative_path for item in walker.discover()}

        assert "build/ignored.log" not in paths
        assert "node_modules/package.js" not in paths

    def test_integrates_with_parser_registry(self, sample_repo: Path) -> None:
        parser_registry = ParserRegistry()
        parser_registry.register(".py", StubParser())

        walker = FileWalker(
            sample_repo,
            parser_registry=parser_registry,
        )
        discovered = {item.relative_path: item.has_registered_parser for item in walker.discover()}

        assert discovered["src/main.py"] is True
        assert discovered["src/App.tsx"] is False

    def test_detects_extensionless_python_via_shebang(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "run").write_bytes(b"#!/usr/bin/env python3\nprint('ok')\n")

        walker = FileWalker(repo)
        discovered = walker.discover()

        assert len(discovered) == 1
        assert discovered[0].relative_path == "run"
        assert discovered[0].language == "python"

    def test_skips_symlink_outside_repository(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        outside = tmp_path / "outside"
        repo.mkdir()
        outside.mkdir()
        (outside / "secret.py").write_text("secret\n", encoding="utf-8")
        (repo / "link.py").symlink_to(outside / "secret.py")

        walker = FileWalker(repo)
        paths = {item.relative_path for item in walker.discover()}

        assert "link.py" not in paths

    def test_non_recursive_walk_only_scans_root(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "root.py").write_text("pass\n", encoding="utf-8")
        (repo / "nested").mkdir()
        (repo / "nested" / "child.py").write_text("pass\n", encoding="utf-8")

        walker = FileWalker(repo, recursive=False)
        paths = {item.relative_path for item in walker.discover()}

        assert paths == {"root.py"}
