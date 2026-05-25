"""Unit tests for platform service (filesystem fallback)."""

from __future__ import annotations

import pytest

from drishti.config import Settings
from drishti.services.platform_service import PlatformService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_workspace_without_postgres(tmp_path) -> None:
    settings = Settings(
        workspaces_cache_root=str(tmp_path / "ws"),
        database_url="",
        enable_minio=False,
    )
    platform = PlatformService.create(settings)
    record = await platform.create_workspace(name="Test", description="demo")
    assert record.id
    listed = await platform.list_workspaces()
    assert any(item.id == record.id for item in listed)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_memory_roundtrip_without_postgres(tmp_path) -> None:
    settings = Settings(
        workspaces_cache_root=str(tmp_path / "ws"),
        database_url="",
        cache_enabled=False,
        enable_minio=False,
    )
    platform = PlatformService.create(settings)
    record = await platform.create_workspace(name="Mem")
    await platform.set_memory(record.id, "prefers pytest")
    assert await platform.get_memory(record.id) == "prefers pytest"
