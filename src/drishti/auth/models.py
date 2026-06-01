"""Authentication data models (US-16.01, US-16.02)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    """Workspace roles for RBAC."""

    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class AuthUser(BaseModel):
    """Authenticated user profile."""

    id: str = Field(description="Unique user identifier")
    email: str = Field(description="User email address")
    name: str | None = Field(default=None, description="Display name")
    picture: str | None = Field(default=None, description="Avatar URL")
    provider: str = Field(description="Auth provider (google, github)")
    provider_id: str = Field(description="ID from the auth provider")
    email_verified: bool = Field(default=False, description="Whether email is verified")


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str = Field(description="Subject (user ID)")
    email: str = Field(description="User email")
    name: str | None = Field(default=None, description="User display name")
    exp: datetime = Field(description="Expiration time")
    iat: datetime = Field(description="Issued at time")
    iss: str = Field(default="drishti", description="Token issuer")
    aud: str = Field(default="drishti-api", description="Token audience")
    provider: str = Field(description="Auth provider")


class WorkspaceRole(BaseModel):
    """User role assignment in a workspace."""

    user_id: str = Field(description="User ID")
    workspace_id: str = Field(description="Workspace ID")
    role: UserRole = Field(description="Assigned role")
    granted_at: datetime = Field(description="When role was granted")
    granted_by: str | None = Field(default=None, description="Who granted the role")


class APIKey(BaseModel):
    """Service account API key."""

    id: str = Field(description="API key ID")
    workspace_id: str = Field(description="Workspace this key belongs to")
    name: str = Field(description="Key name/description")
    key_hash: str = Field(description="Hashed key value")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: str = Field(description="User who created the key")
    last_used: datetime | None = Field(default=None, description="Last usage time")
    expires_at: datetime | None = Field(default=None, description="Optional expiration")
    revoked: bool = Field(default=False, description="Whether key is revoked")
