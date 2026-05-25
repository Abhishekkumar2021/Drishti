"""Arq worker configuration."""

from __future__ import annotations

from typing import Any, ClassVar

from arq.connections import RedisSettings

from drishti.config import get_settings
from drishti.worker.tasks import ingest_workspace_task, shutdown, startup

_settings = get_settings()


class WorkerSettings:
    """Arq worker settings loaded from environment."""

    functions: ClassVar[list[Any]] = [ingest_workspace_task]
    on_startup: ClassVar[Any] = startup
    on_shutdown: ClassVar[Any] = shutdown
    redis_settings: ClassVar[RedisSettings] = RedisSettings.from_dsn(_settings.redis_url)
    max_jobs: ClassVar[int] = 4
    job_timeout: ClassVar[int] = 3600
