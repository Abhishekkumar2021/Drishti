"""OpenTelemetry distributed tracing setup (US-16.04).

Provides automatic instrumentation for FastAPI, httpx, and custom spans
for LangGraph agent operations.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from drishti.config import get_settings

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from opentelemetry.trace import Span, Tracer

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

_tracer: Tracer | None = None


def configure_tracing(
    *,
    service_name: str = "drishti-api",
    otlp_endpoint: str | None = None,
) -> bool:
    """Configure OpenTelemetry tracing with OTLP exporter.

    Args:
        service_name: Name of the service for traces.
        otlp_endpoint: Optional OTLP collector endpoint.

    Returns:
        True if tracing was configured, False if disabled or failed.
    """
    global _tracer

    settings = get_settings()
    if not settings.otel_enabled:
        logger.info("OpenTelemetry tracing disabled (OTEL_ENABLED=false)")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": "1.0.0",
                "deployment.environment": "development" if settings.debug else "production",
            }
        )

        provider = TracerProvider(resource=resource)

        if otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            logger.info("OTLP exporter configured: %s", otlp_endpoint)

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(__name__)

        FastAPIInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()

        logger.info("OpenTelemetry tracing configured for %s", service_name)
        return True

    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-httpx "
            "opentelemetry-exporter-otlp-proto-grpc"
        )
        return False
    except Exception:
        logger.exception("Failed to configure OpenTelemetry tracing")
        return False


def get_tracer() -> Tracer | None:
    """Get the configured tracer, or None if tracing is disabled."""
    return _tracer


@contextmanager
def trace_span(
    name: str,
    *,
    attributes: dict[str, Any] | None = None,
) -> Generator[Span | None, None, None]:
    """Create a tracing span with optional attributes.

    Args:
        name: Name of the span.
        attributes: Optional key-value attributes for the span.

    Yields:
        The span object, or None if tracing is disabled.

    Example:
        with trace_span("process_document", attributes={"file_path": path}):
            # ... processing logic
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        yield span


def traced(
    span_name: str | None = None,
    *,
    record_args: bool = False,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to trace a function execution.

    Args:
        span_name: Optional span name (defaults to function name).
        record_args: Whether to record function arguments as span attributes.

    Example:
        @traced("search_documents")
        def search(query: str, top_k: int) -> list[Document]:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        name = span_name or func.__name__

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            tracer = get_tracer()
            if tracer is None:
                return func(*args, **kwargs)

            attributes: dict[str, Any] = {"function": func.__name__}
            if record_args:
                for i, arg in enumerate(args):
                    attributes[f"arg_{i}"] = str(arg)[:100]
                for key, value in kwargs.items():
                    attributes[f"kwarg_{key}"] = str(value)[:100]

            with tracer.start_as_current_span(name) as span:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:500])
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def traced_async(
    span_name: str | None = None,
    *,
    record_args: bool = False,
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """Async version of the traced decorator.

    Args:
        span_name: Optional span name (defaults to function name).
        record_args: Whether to record function arguments as span attributes.

    Example:
        @traced_async("agent_ask")
        async def ask(query: str) -> str:
            ...
    """

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        name = span_name or func.__name__

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            tracer = get_tracer()
            if tracer is None:
                return await func(*args, **kwargs)

            attributes: dict[str, Any] = {"function": func.__name__}
            if record_args:
                for i, arg in enumerate(args):
                    attributes[f"arg_{i}"] = str(arg)[:100]
                for key, value in kwargs.items():
                    attributes[f"kwarg_{key}"] = str(value)[:100]

            with tracer.start_as_current_span(name) as span:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:500])
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


class AgentSpanContext:
    """Context manager for tracing LangGraph agent operations."""

    def __init__(
        self,
        conversation_id: str,
        *,
        query: str | None = None,
    ) -> None:
        self.conversation_id = conversation_id
        self.query = query
        self._span: Span | None = None

    def __enter__(self) -> AgentSpanContext:
        tracer = get_tracer()
        if tracer is not None:
            self._span = tracer.start_span("agent_conversation")
            self._span.set_attribute("conversation_id", self.conversation_id)
            if self.query:
                self._span.set_attribute("query", self.query[:200])
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._span is not None:
            if exc_type is not None:
                self._span.set_attribute("status", "error")
                self._span.record_exception(exc_val)
            else:
                self._span.set_attribute("status", "success")
            self._span.end()

    def add_retrieval_step(
        self,
        query: str,
        num_results: int,
    ) -> None:
        """Record a retrieval step in the agent trace."""
        if self._span is not None:
            self._span.add_event(
                "retrieval",
                attributes={
                    "query": query[:200],
                    "num_results": num_results,
                },
            )

    def add_generation_step(
        self,
        model: str,
        tokens: int | None = None,
    ) -> None:
        """Record a generation step in the agent trace."""
        if self._span is not None:
            attrs: dict[str, Any] = {"model": model}
            if tokens is not None:
                attrs["tokens"] = tokens
            self._span.add_event("generation", attributes=attrs)
