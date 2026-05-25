"""Unit tests for dependency health probes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from drishti.config import Settings
from drishti.services.health import ServiceStatus, check_embedding

pytestmark = pytest.mark.unit


class TestCheckEmbedding:
    @pytest.mark.asyncio
    async def test_hashing_is_always_connected(self) -> None:
        settings = Settings(_env_file=None, embedding_provider="hashing")
        assert await check_embedding(settings) == ServiceStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_ollama_disconnected_on_connection_error(self) -> None:
        settings = Settings(_env_file=None, embedding_provider="ollama")
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=ConnectionError("refused"))
        with patch("drishti.services.health.httpx.AsyncClient", return_value=mock_client):
            assert await check_embedding(settings) == ServiceStatus.DISCONNECTED
