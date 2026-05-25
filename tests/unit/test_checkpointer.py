"""Unit tests for LangGraph Postgres checkpointer helpers."""

from __future__ import annotations

import pytest

from drishti.agent.checkpointer import psycopg_database_url

pytestmark = pytest.mark.unit


def test_psycopg_database_url_converts_asyncpg_scheme() -> None:
    url = "postgresql+asyncpg://drishti@localhost:5432/drishti"
    assert psycopg_database_url(url) == "postgresql://drishti@localhost:5432/drishti"


def test_psycopg_database_url_passthrough_plain_postgres() -> None:
    url = "postgresql://user:pass@db.example.com:5432/app"
    assert psycopg_database_url(url) == url
