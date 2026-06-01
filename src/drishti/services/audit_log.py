"""Audit logging service for tracking user actions (US-16.05).

Records significant events like ingestion, uploads, memory updates,
and admin actions for compliance and debugging.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AuditAction(StrEnum):
    """Types of auditable actions."""

    INGEST_STARTED = "ingest_started"
    INGEST_COMPLETED = "ingest_completed"
    INGEST_FAILED = "ingest_failed"

    UPLOAD_FILE = "upload_file"
    DELETE_FILE = "delete_file"

    SEARCH_QUERY = "search_query"
    ASK_QUERY = "ask_query"

    MEMORY_CREATE = "memory_create"
    MEMORY_UPDATE = "memory_update"
    MEMORY_DELETE = "memory_delete"

    WORKSPACE_CREATE = "workspace_create"
    WORKSPACE_UPDATE = "workspace_update"
    WORKSPACE_DELETE = "workspace_delete"

    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"

    ADMIN_ACTION = "admin_action"


class AuditEvent(BaseModel):
    """An audit log event."""

    id: str = Field(default="", description="Event ID (auto-generated)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    action: AuditAction = Field(description="Type of action")
    workspace_id: str | None = Field(default=None, description="Workspace context")
    user_id: str | None = Field(default=None, description="User who performed action")
    resource_type: str | None = Field(default=None, description="Type of resource affected")
    resource_id: str | None = Field(default=None, description="ID of resource affected")
    request_id: str | None = Field(default=None, description="HTTP request ID")
    ip_address: str | None = Field(default=None, description="Client IP address")
    user_agent: str | None = Field(default=None, description="Client user agent")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")
    success: bool = Field(default=True, description="Whether action succeeded")
    error_message: str | None = Field(default=None, description="Error message if failed")


class AuditLogService:
    """Service for recording and querying audit events."""

    def __init__(
        self,
        *,
        db_session: AsyncSession | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize the audit log service.

        Args:
            db_session: Optional async database session for persistence.
            enabled: Whether audit logging is enabled.
        """
        self._session = db_session
        self._enabled = enabled
        self._buffer: list[AuditEvent] = []

    async def log(
        self,
        action: AuditAction,
        *,
        workspace_id: str | None = None,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditEvent | None:
        """Record an audit event.

        Args:
            action: The type of action being logged.
            workspace_id: Optional workspace context.
            user_id: Optional user identifier.
            resource_type: Type of resource affected (e.g., "file", "memory").
            resource_id: ID of the affected resource.
            request_id: HTTP request ID for correlation.
            ip_address: Client IP address.
            user_agent: Client user agent string.
            details: Additional event-specific details.
            success: Whether the action succeeded.
            error_message: Error message if the action failed.

        Returns:
            The created audit event, or None if logging is disabled.
        """
        if not self._enabled:
            return None

        import uuid

        event = AuditEvent(
            id=str(uuid.uuid4()),
            action=action,
            workspace_id=workspace_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            success=success,
            error_message=error_message,
        )

        logger.info(
            "Audit: %s %s=%s by user=%s workspace=%s",
            action.value,
            resource_type or "resource",
            resource_id or "unknown",
            user_id or "anonymous",
            workspace_id or "none",
            extra={
                "audit_event": event.model_dump(mode="json"),
            },
        )

        if self._session is not None:
            await self._persist_event(event)
        else:
            self._buffer.append(event)
            if len(self._buffer) > 1000:
                self._buffer = self._buffer[-500:]

        return event

    async def _persist_event(self, event: AuditEvent) -> None:
        """Persist an audit event to the database."""
        if self._session is None:
            return

        try:
            from sqlalchemy import text

            await self._session.execute(
                text("""
                    INSERT INTO audit_events
                    (id, timestamp, action, workspace_id, user_id, resource_type,
                     resource_id, request_id, ip_address, user_agent, details,
                     success, error_message)
                    VALUES
                    (:id, :timestamp, :action, :workspace_id, :user_id, :resource_type,
                     :resource_id, :request_id, :ip_address, :user_agent, :details,
                     :success, :error_message)
                """),
                {
                    "id": event.id,
                    "timestamp": event.timestamp,
                    "action": event.action.value,
                    "workspace_id": event.workspace_id,
                    "user_id": event.user_id,
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id,
                    "request_id": event.request_id,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "details": json.dumps(event.details),
                    "success": event.success,
                    "error_message": event.error_message,
                },
            )
            await self._session.commit()
        except Exception:
            logger.exception("Failed to persist audit event")

    async def query(
        self,
        *,
        workspace_id: str | None = None,
        user_id: str | None = None,
        action: AuditAction | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events with optional filters.

        Args:
            workspace_id: Filter by workspace.
            user_id: Filter by user.
            action: Filter by action type.
            since: Filter events after this time.
            until: Filter events before this time.
            limit: Maximum number of events to return.

        Returns:
            List of matching audit events.
        """
        if self._session is None:
            filtered = self._buffer
            if workspace_id:
                filtered = [e for e in filtered if e.workspace_id == workspace_id]
            if user_id:
                filtered = [e for e in filtered if e.user_id == user_id]
            if action:
                filtered = [e for e in filtered if e.action == action]
            if since:
                filtered = [e for e in filtered if e.timestamp >= since]
            if until:
                filtered = [e for e in filtered if e.timestamp <= until]
            return sorted(filtered, key=lambda e: e.timestamp, reverse=True)[:limit]

        try:
            from sqlalchemy import text

            conditions = ["1=1"]
            params: dict[str, Any] = {"limit": limit}

            if workspace_id:
                conditions.append("workspace_id = :workspace_id")
                params["workspace_id"] = workspace_id
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = user_id
            if action:
                conditions.append("action = :action")
                params["action"] = action.value
            if since:
                conditions.append("timestamp >= :since")
                params["since"] = since
            if until:
                conditions.append("timestamp <= :until")
                params["until"] = until

            query = f"""
                SELECT * FROM audit_events
                WHERE {' AND '.join(conditions)}
                ORDER BY timestamp DESC
                LIMIT :limit
            """

            result = await self._session.execute(text(query), params)
            rows = result.fetchall()

            return [
                AuditEvent(
                    id=row.id,
                    timestamp=row.timestamp,
                    action=AuditAction(row.action),
                    workspace_id=row.workspace_id,
                    user_id=row.user_id,
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    request_id=row.request_id,
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    details=json.loads(row.details) if row.details else {},
                    success=row.success,
                    error_message=row.error_message,
                )
                for row in rows
            ]
        except Exception:
            logger.exception("Failed to query audit events")
            return []


AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action VARCHAR(50) NOT NULL,
    workspace_id UUID REFERENCES workspaces(id),
    user_id VARCHAR(255),
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    request_id VARCHAR(36),
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Indexes for common queries
    CONSTRAINT audit_events_action_check CHECK (action IN (
        'ingest_started', 'ingest_completed', 'ingest_failed',
        'upload_file', 'delete_file',
        'search_query', 'ask_query',
        'memory_create', 'memory_update', 'memory_delete',
        'workspace_create', 'workspace_update', 'workspace_delete',
        'user_login', 'user_logout', 'api_key_create', 'api_key_revoke',
        'admin_action'
    ))
);

CREATE INDEX IF NOT EXISTS idx_audit_events_workspace ON audit_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_action ON audit_events(action);
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp DESC);
"""
