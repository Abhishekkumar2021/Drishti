"""Unit tests for git incremental indexing (US-03.10)."""

from __future__ import annotations

from pathlib import Path

import pytest
from git import Repo

from drishti.exceptions import GitRepositoryError
from drishti.ingestion.ast.registry import create_default_parser_registry
from drishti.ingestion.chunk_index import InMemoryChunkIndex
from drishti.ingestion.git_changes import (
    discover_parseable_files,
    resolve_changes,
    resolve_head_commit,
)
from drishti.ingestion.incremental import IncrementalIndexer
from drishti.ingestion.index_state import IndexStateStore

pytestmark = pytest.mark.unit


def _init_repo(path: Path) -> Repo:
    repo = Repo.init(path)
    with repo.config_writer() as config:
        config.set_value("user", "email", "dev@drishti.local")
        config.set_value("user", "name", "Drishti Test")
    return repo


def _commit_all(repo: Repo, message: str) -> str:
    repo.git.add(all=True)
    commit = repo.index.commit(message)
    return str(commit.hexsha)


class TestGitChanges:
    def test_resolve_changes_detects_added_modified_deleted(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        first_file = tmp_path / "alpha.py"
        first_file.write_text("def alpha():\n    return 1\n", encoding="utf-8")
        first_commit = _commit_all(repo, "add alpha")

        second_file = tmp_path / "beta.py"
        second_file.write_text("def beta():\n    return 2\n", encoding="utf-8")
        first_file.write_text("def alpha():\n    return 99\n", encoding="utf-8")
        _commit_all(repo, "add beta and modify alpha")

        first_file.unlink()
        _commit_all(repo, "delete alpha")

        changes = resolve_changes(tmp_path, indexed_commit=first_commit)
        assert "alpha.py" in changes.deleted
        assert "beta.py" in changes.added

    def test_resolve_changes_full_index_when_no_base(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        sample = tmp_path / "sample.py"
        sample.write_text("def run():\n    pass\n", encoding="utf-8")
        _commit_all(repo, "initial")

        registry = create_default_parser_registry()
        parseable = discover_parseable_files(tmp_path, parser_registry=registry)
        changes = resolve_changes(tmp_path, indexed_commit=None, parseable_paths=parseable)
        assert changes.is_full_reindex is True
        assert "sample.py" in changes.added

    def test_resolve_head_commit(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        (tmp_path / "main.py").write_text("pass\n", encoding="utf-8")
        commit = _commit_all(repo, "init")
        assert resolve_head_commit(tmp_path) == commit

    def test_non_repo_raises(self, tmp_path: Path) -> None:
        with pytest.raises(GitRepositoryError):
            resolve_head_commit(tmp_path)


class TestIncrementalIndexer:
    def test_first_run_indexes_parseable_files(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        (tmp_path / "service.py").write_text(
            "class Service:\n    def run(self):\n        return True\n",
            encoding="utf-8",
        )
        _commit_all(repo, "initial")

        registry = create_default_parser_registry()
        chunk_index = InMemoryChunkIndex()
        indexer = IncrementalIndexer(tmp_path, parser_registry=registry, chunk_index=chunk_index)
        result = indexer.run()

        assert result.files_parsed == 1
        assert result.chunks_indexed >= 1
        assert chunk_index.count() >= 1
        state = IndexStateStore.for_repository(tmp_path).load()
        assert state is not None
        assert state.indexed_commit == result.head_commit

    def test_incremental_run_handles_modification_and_deletion(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        target = tmp_path / "worker.py"
        target.write_text("def work():\n    return 1\n", encoding="utf-8")
        _commit_all(repo, "add worker")

        registry = create_default_parser_registry()
        chunk_index = InMemoryChunkIndex()
        indexer = IncrementalIndexer(tmp_path, parser_registry=registry, chunk_index=chunk_index)
        indexer.run()
        assert chunk_index.count() >= 1

        target.write_text(
            "def work():\n    if True:\n        return 2\n    return 0\n",
            encoding="utf-8",
        )
        _commit_all(repo, "modify worker")

        modify_result = indexer.run()
        assert modify_result.modified == ("worker.py",)
        assert modify_result.chunks_indexed >= 1

        target.unlink()
        _commit_all(repo, "remove worker")

        delete_result = indexer.run()
        assert delete_result.deleted == ("worker.py",)
        assert delete_result.chunks_removed >= 1
        assert chunk_index.count() == 0

    def test_force_full_reindexes_repository(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path)
        (tmp_path / "app.py").write_text("def app():\n    pass\n", encoding="utf-8")
        _commit_all(repo, "initial")

        registry = create_default_parser_registry()
        chunk_index = InMemoryChunkIndex()
        indexer = IncrementalIndexer(tmp_path, parser_registry=registry, chunk_index=chunk_index)
        indexer.run()

        (tmp_path / "app.py").unlink()
        _commit_all(repo, "delete without incremental")
        indexer.run()
        assert chunk_index.count() == 0

        (tmp_path / "app.py").write_text("def app():\n    return 1\n", encoding="utf-8")
        _commit_all(repo, "restore")
        full = indexer.run(force_full=True)
        assert full.base_commit is None
        assert chunk_index.count() >= 1
