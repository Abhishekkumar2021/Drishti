"""Bind request context into structured logs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from drishti.observability.logging import bind_context, clear_context


class LoggingContextMiddleware(BaseHTTPMiddleware):
    """Attach request_id and path to structlog contextvars."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = getattr(request.state, "request_id", None)
        bind_context(
            request_id=request_id,
            http_method=request.method,
            http_path=request.url.path,
        )
        try:
            return await call_next(request)
        finally:
            clear_context()
