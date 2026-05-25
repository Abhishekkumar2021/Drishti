"""Drishti — दृष्टि — FastAPI Application.

Multi-modal, AST-aware RAG system for code & document understanding.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from drishti import __version__
from drishti.agent.runner import AgentRunner
from drishti.api.platform_routes import router as platform_router
from drishti.api.responses import ErrorDetail, ErrorResponse, HealthResponse, LivenessResponse
from drishti.api.routes import router as api_router
from drishti.config import Settings, get_settings
from drishti.exceptions import DrishtiError
from drishti.middleware.auth import BearerAuthMiddleware
from drishti.middleware.logging_context import LoggingContextMiddleware
from drishti.middleware.rate_limit import RateLimitMiddleware
from drishti.middleware.request_id import RequestIdMiddleware
from drishti.observability.logging import configure_structured_logging, get_logger
from drishti.services.health import ServiceStatus, probe_dependencies
from drishti.services.platform_service import PlatformService
from drishti.services.query_cache import QueryCache
from drishti.services.wiring import create_qdrant_client, create_rag_pipeline

log = get_logger(__name__)


def configure_logging(settings: Settings) -> None:
    """Configure structured or plain logging."""
    if settings.structured_logging:
        configure_structured_logging(
            level=settings.log_level,
            json_logs=settings.log_json,
            service_name=settings.otel_service_name,
        )
    else:
        import logging

        logging.basicConfig(
            level=settings.log_level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory for Drishti."""
    app_settings = settings or get_settings()
    configure_logging(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        log.info("drishti_starting", version=__version__)
        app_settings.validate_runtime_configuration()
        for key, value in app_settings.runtime_provider_summary().items():
            log.info("config", key=key, value=value)
        if app_settings.llm_provider == "mock":
            log.warning(
                "llm_mock_enabled",
                hint="Set LLM_PROVIDER=ollama or anthropic in .env for real Q&A",
            )
        log.info(
            "infrastructure",
            qdrant=app_settings.qdrant_url,
            collection=app_settings.qdrant_collection_name,
            postgres=app_settings.postgres_enabled,
            minio=app_settings.minio_enabled,
        )
        if app_settings.api_auth_enabled:
            log.info("api_auth_enabled")
        else:
            log.warning("api_auth_disabled", hint="Set API_TOKEN for production")

        qdrant_client = create_qdrant_client(app_settings)
        app.state.qdrant_client = qdrant_client
        app.state.query_cache = QueryCache(
            app_settings.redis_url,
            ttl_seconds=app_settings.cache_ttl_seconds,
            enabled=app_settings.cache_enabled,
        )
        app.state.platform_service = PlatformService.create(app_settings)
        rag = create_rag_pipeline(app_settings, client=qdrant_client)
        app.state.rag_pipeline = rag
        app.state.agent_runner = AgentRunner(rag, app_settings)

        yield

        qdrant_client.close()
        log.info("drishti_shutdown")

    docs_url = "/docs" if app_settings.enable_openapi_docs else None
    redoc_url = "/redoc" if app_settings.enable_openapi_docs else None

    application = FastAPI(
        title="Drishti — दृष्टि",
        description=(
            "Multi-modal, AST-aware RAG system for code & document understanding. "
            "Parse codebases via Tree-sitter into semantic chunks, ingest PDFs/docs/diagrams, "
            "and query everything with hybrid BM25+vector search."
        ),
        version=__version__,
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )

    application.add_middleware(LoggingContextMiddleware)
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(RateLimitMiddleware, settings=app_settings)
    application.add_middleware(BearerAuthMiddleware, settings=app_settings)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)
    register_health_routes(application, app_settings)
    application.include_router(api_router)
    application.include_router(platform_router)
    return application


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(DrishtiError)
    async def drishti_error_handler(request: Request, exc: DrishtiError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        status_code = 400
        if exc.code == "AUTHENTICATION_ERROR":
            status_code = 401
        elif exc.code == "AUTHORIZATION_ERROR":
            status_code = 403
        elif exc.code == "CONFIGURATION_ERROR":
            status_code = 500
        elif exc.code in ("GENERATION_ERROR", "SEARCH_ERROR", "EMBEDDING_ERROR"):
            status_code = 502
        elif exc.code in ("PATH_VALIDATION_ERROR", "GIT_REPOSITORY_ERROR", "INGESTION_ERROR"):
            status_code = 400
        elif exc.code == "SERVICE_UNAVAILABLE":
            status_code = 503

        log.warning(
            "drishti_error",
            code=exc.code,
            message=exc.message,
            request_id=request_id,
            status_code=status_code,
        )
        payload = ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                request_id=request_id,
            ),
        )
        return JSONResponse(status_code=status_code, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        log.exception("unhandled_error", request_id=request_id, error=str(exc))
        payload = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                request_id=request_id,
            ),
        )
        return JSONResponse(status_code=500, content=payload.model_dump())


def register_health_routes(app: FastAPI, settings: Settings) -> None:
    """Register liveness and readiness health endpoints."""

    async def liveness() -> LivenessResponse:
        return LivenessResponse(version=__version__)

    async def readiness() -> Response:
        services = await probe_dependencies(settings)
        service_map = {name: status.value for name, status in services.items()}
        critical = (services["qdrant"], services["redis"])
        if all(status == ServiceStatus.CONNECTED for status in critical):
            overall = "healthy"
            status_code = 200
        elif any(status == ServiceStatus.CONNECTED for status in critical):
            overall = "degraded"
            status_code = 200
        else:
            overall = "unhealthy"
            status_code = 503

        payload = HealthResponse(
            status=overall,  # type: ignore[arg-type]
            services=service_map,
            version=__version__,
        )
        return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))

    for path in ("/health/live", "/api/v1/health/live"):
        app.add_api_route(path, liveness, methods=["GET"], tags=["System"])

    for path in ("/health", "/health/ready", "/api/v1/health", "/api/v1/health/ready"):
        app.add_api_route(path, readiness, methods=["GET"], tags=["System"])


app = create_app()


def main() -> None:
    """Entry point for the CLI."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "drishti.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
