"""Drishti — दृष्टि — FastAPI Application.

Multi-modal, AST-aware RAG system for code & document understanding.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from drishti import __version__
from drishti.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logger.info("🔮 Drishti v%s starting...", __version__)
    logger.info("   Qdrant: %s:%s", settings.qdrant_host, settings.qdrant_port)
    logger.info("   Collection: %s", settings.qdrant_collection_name)

    # TODO: Initialize Qdrant client
    # TODO: Initialize Redis client
    # TODO: Verify connections

    logger.info("✅ Drishti ready — see through your codebase")
    yield
    logger.info("👋 Drishti shutting down...")


app = FastAPI(
    title="Drishti — दृष्टि",
    description=(
        "Multi-modal, AST-aware RAG system for code & document understanding. "
        "Parse codebases via Tree-sitter into semantic chunks, ingest PDFs/docs/diagrams, "
        "and query everything with hybrid BM25+vector search."
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS Middleware ─────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ────────────────────────────
@app.get("/api/v1/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "service": "drishti",
    }


# ─── Route Registration ─────────────────────
# Uncomment as routes are implemented:
# from drishti.api.routes import ingest, search, ask
# app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
# app.include_router(search.router, prefix="/api/v1", tags=["Search"])
# app.include_router(ask.router, prefix="/api/v1", tags=["RAG"])


def main() -> None:
    """Entry point for the CLI."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "drishti.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
