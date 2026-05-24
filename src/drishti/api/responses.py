"""API response models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    """Health status for a single infrastructure dependency."""

    status: Literal["connected", "disconnected", "disabled", "not_configured"]


class HealthResponse(BaseModel):
    """Readiness health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    services: dict[str, str]
    version: str
    service: str = "drishti"


class LivenessResponse(BaseModel):
    """Liveness probe response."""

    status: Literal["alive"] = "alive"
    version: str
    service: str = "drishti"


class ErrorDetail(BaseModel):
    """Structured API error payload."""

    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Top-level error response envelope."""

    error: ErrorDetail
