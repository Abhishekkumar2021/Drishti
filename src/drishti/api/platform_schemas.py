"""Schemas for workspaces, artifacts, conversations, and memory."""

from __future__ import annotations

from pydantic import BaseModel, Field

from drishti.api.schemas import ChatMessage


class WorkspaceCreateRequest(BaseModel):
    """Create an isolated knowledge workspace."""

    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""


class WorkspaceResponse(BaseModel):
    """Workspace metadata."""

    id: str
    name: str
    created_at: str
    description: str = ""
    sources: list[str] = Field(default_factory=list)


class WorkspaceMemoryRequest(BaseModel):
    """Update durable agent memory for a workspace."""

    memory: str = Field(..., max_length=16_000)


class WorkspaceMemoryResponse(BaseModel):
    """Stored workspace memory."""

    workspace_id: str
    memory: str


class ConversationCreateRequest(BaseModel):
    """Start a server-persisted chat session."""

    workspace_id: str | None = None
    title: str = ""


class ConversationResponse(BaseModel):
    """Conversation metadata."""

    id: str
    workspace_id: str | None = None
    title: str
    created_at: str
    updated_at: str


class ConversationAskRequest(BaseModel):
    """Ask within a persisted conversation (history loaded server-side)."""

    question: str = Field(..., min_length=1)
    stream: bool = True


class ConversationMessagesResponse(BaseModel):
    """Full message list for a conversation."""

    conversation_id: str
    messages: list[ChatMessage]


class ArtifactUploadResponse(BaseModel):
    """Result of uploading files into a workspace."""

    workspace_id: str
    saved_files: list[str]
    head_commit: str | None = None
