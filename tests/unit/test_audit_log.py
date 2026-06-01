"""Unit tests for audit log service (US-16.05)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from drishti.services.audit_log import AuditAction, AuditEvent, AuditLogService


class TestAuditAction:
    """Test audit action enum."""

    def test_ingest_actions(self) -> None:
        """AuditAction should have ingest-related actions."""
        assert AuditAction.INGEST_STARTED == "ingest_started"
        assert AuditAction.INGEST_COMPLETED == "ingest_completed"
        assert AuditAction.INGEST_FAILED == "ingest_failed"

    def test_file_actions(self) -> None:
        """AuditAction should have file-related actions."""
        assert AuditAction.UPLOAD_FILE == "upload_file"
        assert AuditAction.DELETE_FILE == "delete_file"

    def test_query_actions(self) -> None:
        """AuditAction should have query-related actions."""
        assert AuditAction.SEARCH_QUERY == "search_query"
        assert AuditAction.ASK_QUERY == "ask_query"

    def test_memory_actions(self) -> None:
        """AuditAction should have memory-related actions."""
        assert AuditAction.MEMORY_CREATE == "memory_create"
        assert AuditAction.MEMORY_UPDATE == "memory_update"
        assert AuditAction.MEMORY_DELETE == "memory_delete"

    def test_auth_actions(self) -> None:
        """AuditAction should have auth-related actions."""
        assert AuditAction.USER_LOGIN == "user_login"
        assert AuditAction.USER_LOGOUT == "user_logout"
        assert AuditAction.API_KEY_CREATE == "api_key_create"
        assert AuditAction.API_KEY_REVOKE == "api_key_revoke"


class TestAuditEvent:
    """Test audit event model."""

    def test_create_event(self) -> None:
        """AuditEvent should be creatable with required fields."""
        event = AuditEvent(
            action=AuditAction.SEARCH_QUERY,
        )
        assert event.action == AuditAction.SEARCH_QUERY
        assert event.success is True
        assert event.timestamp is not None

    def test_event_with_all_fields(self) -> None:
        """AuditEvent should accept all optional fields."""
        event = AuditEvent(
            id="evt-123",
            action=AuditAction.INGEST_COMPLETED,
            workspace_id="ws-456",
            user_id="user-789",
            resource_type="file",
            resource_id="file-abc",
            request_id="req-def",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            details={"file_count": 10},
            success=True,
        )
        assert event.workspace_id == "ws-456"
        assert event.user_id == "user-789"
        assert event.details["file_count"] == 10

    def test_event_with_error(self) -> None:
        """AuditEvent should capture error information."""
        event = AuditEvent(
            action=AuditAction.INGEST_FAILED,
            success=False,
            error_message="File not found",
        )
        assert event.success is False
        assert event.error_message == "File not found"


class TestAuditLogService:
    """Test audit log service."""

    @pytest.fixture
    def service(self) -> AuditLogService:
        """Create an audit log service for testing."""
        return AuditLogService(enabled=True)

    @pytest.fixture
    def disabled_service(self) -> AuditLogService:
        """Create a disabled audit log service."""
        return AuditLogService(enabled=False)

    @pytest.mark.asyncio
    async def test_log_event(self, service: AuditLogService) -> None:
        """Service should log events to buffer."""
        event = await service.log(
            AuditAction.SEARCH_QUERY,
            user_id="user123",
            workspace_id="ws456",
            details={"query": "test"},
        )

        assert event is not None
        assert event.action == AuditAction.SEARCH_QUERY
        assert event.user_id == "user123"
        assert event.workspace_id == "ws456"

    @pytest.mark.asyncio
    async def test_log_disabled(self, disabled_service: AuditLogService) -> None:
        """Disabled service should not log events."""
        event = await disabled_service.log(
            AuditAction.SEARCH_QUERY,
            user_id="user123",
        )
        assert event is None

    @pytest.mark.asyncio
    async def test_query_events(self, service: AuditLogService) -> None:
        """Service should query buffered events."""
        await service.log(AuditAction.SEARCH_QUERY, user_id="user1")
        await service.log(AuditAction.ASK_QUERY, user_id="user1")
        await service.log(AuditAction.SEARCH_QUERY, user_id="user2")

        results = await service.query(user_id="user1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_by_action(self, service: AuditLogService) -> None:
        """Service should filter by action type."""
        await service.log(AuditAction.SEARCH_QUERY)
        await service.log(AuditAction.ASK_QUERY)
        await service.log(AuditAction.SEARCH_QUERY)

        results = await service.query(action=AuditAction.SEARCH_QUERY)
        assert len(results) == 2
        assert all(r.action == AuditAction.SEARCH_QUERY for r in results)

    @pytest.mark.asyncio
    async def test_query_by_workspace(self, service: AuditLogService) -> None:
        """Service should filter by workspace."""
        await service.log(AuditAction.SEARCH_QUERY, workspace_id="ws1")
        await service.log(AuditAction.SEARCH_QUERY, workspace_id="ws2")
        await service.log(AuditAction.SEARCH_QUERY, workspace_id="ws1")

        results = await service.query(workspace_id="ws1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_by_time_range(self, service: AuditLogService) -> None:
        """Service should filter by time range."""
        now = datetime.now(UTC)
        await service.log(AuditAction.SEARCH_QUERY)

        results_after = await service.query(since=now - timedelta(hours=1))
        assert len(results_after) >= 1

        results_before = await service.query(until=now - timedelta(hours=1))
        assert len(results_before) == 0

    @pytest.mark.asyncio
    async def test_query_limit(self, service: AuditLogService) -> None:
        """Service should respect query limit."""
        for _ in range(10):
            await service.log(AuditAction.SEARCH_QUERY)

        results = await service.query(limit=5)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_buffer_pruning(self, service: AuditLogService) -> None:
        """Service should prune old events from buffer."""
        for i in range(1100):
            await service.log(AuditAction.SEARCH_QUERY, user_id=f"user{i}")

        assert len(service._buffer) <= 1000

    @pytest.mark.asyncio
    async def test_log_with_request_context(self, service: AuditLogService) -> None:
        """Service should capture request context."""
        event = await service.log(
            AuditAction.INGEST_STARTED,
            request_id="req-123",
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
        )

        assert event is not None
        assert event.request_id == "req-123"
        assert event.ip_address == "10.0.0.1"
        assert event.user_agent == "Mozilla/5.0"
