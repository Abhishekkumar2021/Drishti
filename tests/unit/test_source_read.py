"""Unit tests for source file read API (EPIC-10)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from drishti.config import Settings
from drishti.main import create_app
from drishti.services.health import ServiceStatus

pytestmark = pytest.mark.unit


@pytest.fixture
def api_client(tmp_path: Path) -> TestClient:
    repo = tmp_path / "sample-repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "auth.py").write_text("def login():\n    pass\n", encoding="utf-8")

    settings = Settings(
        api_token="",
        debug=True,
        cache_enabled=False,
        rate_limit_enabled=False,
        ingestion_allowed_roots=[str(tmp_path)],
    )
    services = {
        "qdrant": ServiceStatus.CONNECTED,
        "redis": ServiceStatus.CONNECTED,
        "neo4j": ServiceStatus.DISABLED,
    }
    mock_search = MagicMock()
    with (
        patch("drishti.main.probe_dependencies", new=AsyncMock(return_value=services)),
        patch("drishti.main.create_qdrant_client", return_value=MagicMock()),
        patch("drishti.api.deps.create_hybrid_search", return_value=mock_search),
        patch("drishti.api.deps.create_rag_pipeline", return_value=MagicMock()),
    ):
        app = create_app(settings)
        with TestClient(app, raise_server_exceptions=True) as client:
            client.test_repo = repo  # type: ignore[attr-defined]
            yield client


class TestSourceRead:
    def test_reads_file_within_repo(self, api_client: TestClient) -> None:
        repo: Path = api_client.test_repo  # type: ignore[attr-defined]
        response = api_client.post(
            "/api/v1/source/read",
            json={"repo_path": str(repo), "file_path": "src/auth.py"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "def login" in body["content"]
        assert body["language"] == "python"

    def test_rejects_path_traversal(self, api_client: TestClient) -> None:
        repo: Path = api_client.test_repo  # type: ignore[attr-defined]
        response = api_client.post(
            "/api/v1/source/read",
            json={"repo_path": str(repo), "file_path": "../outside.py"},
        )
        assert response.status_code == 400
