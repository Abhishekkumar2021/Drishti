"""Unit tests for LangChain agent tools."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from drishti.agent.tools import AgentToolRuntime, build_agent_tools
from drishti.config import Settings
from drishti.ingestion.index_state import IndexState, IndexStateStore
from drishti.search.models import SearchHit
from drishti.services.platform_service import PlatformService

pytestmark = pytest.mark.unit


def test_build_agent_tools_registers_three_tools() -> None:
    runtime = AgentToolRuntime(settings=Settings(), search=MagicMock())
    tools = build_agent_tools(runtime)
    names = {tool.name for tool in tools}
    assert names == {"hybrid_search", "read_source", "ingest_status"}


def test_hybrid_search_tool_returns_json_hits() -> None:
    mock_search = MagicMock()
    mock_search.search.return_value = [
        SearchHit(
            chunk_id="c1",
            score=0.9,
            content="def auth(): pass",
            payload={"file_path": "src/auth.py", "start_line": 1, "end_line": 3},
            source="rerank",
        ),
    ]
    runtime = AgentToolRuntime(settings=Settings(), search=mock_search)
    tool = build_agent_tools(runtime)[0]
    raw = tool.invoke({"query": "auth", "workspace_id": "ws-1", "limit": 5})
    payload = json.loads(raw)
    assert payload["results"][0]["file_path"] == "src/auth.py"
    mock_search.search.assert_called_once()
    call_kwargs = mock_search.search.call_args.kwargs
    assert call_kwargs["filters"] == {"file_path": "workspaces/ws-1/*"}


def test_read_source_tool_reads_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")

    settings = Settings(ingestion_allowed_roots=[str(tmp_path)])
    runtime = AgentToolRuntime(settings=settings, search=MagicMock())
    tool = next(t for t in build_agent_tools(runtime) if t.name == "read_source")
    raw = tool.invoke({"repo_path": str(repo), "file_path": "src/main.py"})
    payload = json.loads(raw)
    assert "print" in payload["content"]
    assert payload["language"] == "python"


@pytest.mark.asyncio
async def test_ingest_status_tool_reports_index_state(tmp_path: Path) -> None:
    settings = Settings(
        workspaces_cache_root=str(tmp_path / "ws"),
        database_url="",
        enable_minio=False,
        cache_enabled=False,
    )
    platform = PlatformService.create(settings)
    record = await platform.create_workspace(name="Docs")
    ingest_root = platform.ingest_root(record.id)
    IndexStateStore.for_repository(ingest_root).save(
        IndexState(indexed_commit="abc123", files={"a.py": "hash1"}),
    )

    runtime = AgentToolRuntime(settings=settings, search=MagicMock(), platform=platform)
    tool = next(t for t in build_agent_tools(runtime) if t.name == "ingest_status")
    raw = tool.invoke({"workspace_id": record.id})
    payload = json.loads(raw)
    assert payload["indexed"] is True
    assert payload["indexed_commit"] == "abc123"
    assert payload["files_tracked"] == 1
