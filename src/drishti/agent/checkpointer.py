"""LangGraph Postgres checkpointer factory."""

from __future__ import annotations

import logging
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING

from drishti.config import Settings

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres import PostgresSaver

logger = logging.getLogger(__name__)


def psycopg_database_url(database_url: str) -> str:
    """Convert SQLAlchemy async URL to a psycopg-compatible connection string."""
    url = database_url.strip()
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if url.startswith(prefix):
            return f"postgresql://{url[len(prefix):]}"
    return url


def open_postgres_checkpointer(
    settings: Settings,
) -> AbstractContextManager[PostgresSaver]:
    """Open a long-lived PostgresSaver context (call ``__enter__`` in app lifespan)."""
    from langgraph.checkpoint.postgres import PostgresSaver

    uri = psycopg_database_url(settings.database_url)
    logger.info("langgraph_checkpointer_opening")
    return PostgresSaver.from_conn_string(uri)


def setup_postgres_checkpointer(checkpointer: PostgresSaver) -> None:
    """Create checkpoint tables (idempotent). Must run before first graph invoke."""
    checkpointer.setup()
