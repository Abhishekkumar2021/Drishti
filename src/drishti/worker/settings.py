"""Arq worker configuration."""

from __future__ import annotations

from arq.connections import RedisSettings

from drishti.config import get_settings
from drishti.worker.tasks import ingest_workspace_task, shutdown, startup

_settings = get_settings()


class WorkerSettings:
    """Arq worker settings loaded from environment."""

    functions = [ingest_workspace_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(_settings.redis_url)
    max_jobs = 4
    job_timeout = 3600
