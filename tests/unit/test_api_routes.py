"""Unit tests for API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from drishti.api.responses import AskResponse, SearchResponse
from drishti.config import Settings
from drishti.generation.models import Citation, ContextChunk, RAGAnswer
from drishti.main import create_app
from drishti.search.models import SearchHit
from drishti.services.health import ServiceStatus
from drishti.services.query_cache import QueryCache

pytestmark = pytest.mark.unit


@pytest.fixture
def api_client() -> TestClient:
    settings = Settings(api_token="", debug=True, cache_enabled=False, rate_limit_enabled=False)
    services = {
        "qdrant": ServiceStatus.CONNECTED,
        "redis": ServiceStatus.CONNECTED,
        "neo4j": ServiceStatus.DISABLED,
    }
    mock_search = MagicMock()
    mock_search.search.return_value = [
        SearchHit(
            chunk_id="c1",
            score=0.9,
            content="def auth(): pass",
            payload={"file_path": "src/auth.py", "start_line": 1, "end_line": 3},
            source="rerank",
        )
    ]

    mock_rag = MagicMock()
    mock_rag.ask_stream.return_value = iter([])
    mock_rag.ask.return_value = RAGAnswer(
        question="Where is auth?",
        answer="See [src/auth.py:L1-3].",
        citations=(
            Citation(
                citation_tag="[src/auth.py:L1-3]",
                file_path="src/auth.py",
                start_line=1,
                end_line=3,
                valid=True,
            ),
        ),
        context_chunks=(
            ContextChunk(
                chunk_id="c1",
                file_path="src/auth.py",
                content="def auth(): pass",
                start_line=1,
                end_line=3,
            ),
        ),
    )

    with (
        patch("drishti.main.probe_dependencies", new=AsyncMock(return_value=services)),
        patch("drishti.main.create_qdrant_client") as mock_qdrant,
        patch("drishti.api.deps.create_hybrid_search", return_value=mock_search),
        patch("drishti.api.deps.create_rag_pipeline", return_value=mock_rag),
    ):
        mock_qdrant.return_value = MagicMock()
        app = create_app(settings)
        app.state.query_cache = QueryCache(settings.redis_url, enabled=False)
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client


class TestSearchRoute:
    def test_search_returns_results(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/api/v1/search",
            json={"query": "authentication", "limit": 5},
        )
        assert response.status_code == 200
        body = SearchResponse.model_validate(response.json())
        assert body.query == "authentication"
        assert len(body.results) == 1
        assert body.results[0].file_path == "src/auth.py"


class TestAskRoute:
    def test_ask_non_streaming_returns_answer(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/api/v1/ask?stream=false",
            json={"question": "Where is auth?"},
        )
        assert response.status_code == 200
        body = AskResponse.model_validate(response.json())
        assert "auth" in body.answer.lower()
        assert len(body.citations) == 1

    def test_ask_streaming_returns_sse(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/api/v1/ask",
            json={"question": "Where is auth?"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


class TestIngestRoute:
    def test_ingest_validates_repo_path(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/api/v1/ingest",
            json={"repo_path": "/nonexistent/path/that/does/not/exist"},
        )
        assert response.status_code in {400, 422}
