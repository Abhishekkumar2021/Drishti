"""Arq background tasks for ingest and maintenance."""

from __future__ import annotations

import logging
from typing import Any

from drishti.config import get_settings
from drishti.services.wiring import create_incremental_indexer, create_qdrant_client

logger = logging.getLogger(__name__)


async def ingest_workspace_task(
    ctx: dict[str, Any],
    *,
    repo_path: str,
    path_prefix: str,
    force_full: bool = False,
) -> dict[str, object]:
    """Run incremental indexing in a worker process."""
    settings = get_settings()
    client = create_qdrant_client(settings)
    try:
        from pathlib import Path

        indexer = create_incremental_indexer(
            settings,
            Path(repo_path),
            client=client,
            path_prefix=path_prefix,
        )
        result = indexer.run(force_full=force_full)
        logger.info(
            "Ingest complete path_prefix=%s chunks=%s",
            path_prefix,
            result.chunks_indexed,
        )
        return {
            "chunks_indexed": result.chunks_indexed,
            "total_chunks_in_store": result.total_chunks_in_store,
            "up_to_date": result.up_to_date,
            "parseable_files": result.parseable_files,
        }
    finally:
        client.close()


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup hook."""
    logger.info("Drishti worker started")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown hook."""
    logger.info("Drishti worker stopped")
