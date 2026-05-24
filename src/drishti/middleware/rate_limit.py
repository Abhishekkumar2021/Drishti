"""Redis-backed per-client rate limiting (US-08.04)."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from drishti.config import Settings, get_settings

logger = logging.getLogger(__name__)

_EXEMPT_PATHS = frozenset(
    {
        "/health",
        "/health/live",
        "/health/ready",
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit API requests per minute using Redis counters."""

    def __init__(self, app: ASGIApp, settings: Settings | None = None) -> None:
        super().__init__(app)
        self._settings = settings or get_settings()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not self._settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if path in _EXEMPT_PATHS or not path.startswith("/api/v1"):
            return await call_next(request)

        client_id = _client_identifier(request)
        window = int(time.time() // 60)
        key = f"drishti:ratelimit:{client_id}:{window}"
        limit = max(1, self._settings.rate_limit_requests_per_minute)

        redis_client = aioredis.from_url(
            self._settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        try:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, 120)
            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests; try again later",
                        }
                    },
                    headers={"Retry-After": "60"},
                )
        except Exception:
            logger.warning("Rate limit check failed; allowing request", exc_info=True)
        finally:
            await redis_client.aclose()

        return await call_next(request)


def _client_identifier(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"
