"""Unit tests for authentication modules (EPIC-16)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from drishti.auth.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    decode_token,
    verify_token,
)
from drishti.auth.models import AuthUser, TokenPayload, UserRole, WorkspaceRole
from drishti.auth.oidc import (
    GitHubOIDCProvider,
    GoogleOIDCProvider,
    get_enabled_providers,
)


class TestAuthModels:
    """Test authentication data models."""

    def test_auth_user_creation(self) -> None:
        """AuthUser should be creatable with required fields."""
        user = AuthUser(
            id="google:123",
            email="test@example.com",
            provider="google",
            provider_id="123",
        )
        assert user.id == "google:123"
        assert user.email == "test@example.com"
        assert user.provider == "google"
        assert user.email_verified is False

    def test_auth_user_with_optional_fields(self) -> None:
        """AuthUser should accept optional fields."""
        user = AuthUser(
            id="github:456",
            email="dev@example.com",
            name="Developer",
            picture="https://avatars.example.com/456",
            provider="github",
            provider_id="456",
            email_verified=True,
        )
        assert user.name == "Developer"
        assert user.picture is not None
        assert user.email_verified is True

    def test_token_payload(self) -> None:
        """TokenPayload should contain JWT claims."""
        now = datetime.now(UTC)
        payload = TokenPayload(
            sub="user123",
            email="test@example.com",
            name="Test User",
            exp=now + timedelta(hours=1),
            iat=now,
            provider="google",
        )
        assert payload.sub == "user123"
        assert payload.iss == "drishti"
        assert payload.aud == "drishti-api"

    def test_user_role_enum(self) -> None:
        """UserRole should define workspace roles."""
        assert UserRole.OWNER == "owner"
        assert UserRole.EDITOR == "editor"
        assert UserRole.VIEWER == "viewer"

    def test_workspace_role(self) -> None:
        """WorkspaceRole should assign roles to users."""
        role = WorkspaceRole(
            user_id="user123",
            workspace_id="ws456",
            role=UserRole.EDITOR,
            granted_at=datetime.now(UTC),
        )
        assert role.role == UserRole.EDITOR


class TestJWTUtils:
    """Test JWT token creation and verification."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings with JWT config."""
        settings = MagicMock()
        settings.jwt_secret_key = "test-secret-key-for-jwt-testing-only"
        settings.jwt_access_token_expire_minutes = 30
        return settings

    @pytest.fixture
    def test_user(self) -> AuthUser:
        """Create a test user."""
        return AuthUser(
            id="test:123",
            email="test@example.com",
            name="Test User",
            provider="test",
            provider_id="123",
        )

    def test_create_and_decode_token(
        self,
        mock_settings: MagicMock,
        test_user: AuthUser,
    ) -> None:
        """Token creation and decoding should round-trip."""
        with patch("drishti.auth.jwt_utils.get_settings", return_value=mock_settings):
            token = create_access_token(test_user)
            payload = decode_token(token)

        assert payload is not None
        assert payload.sub == test_user.id
        assert payload.email == test_user.email
        assert payload.provider == test_user.provider

    def test_verify_token_valid(
        self,
        mock_settings: MagicMock,
        test_user: AuthUser,
    ) -> None:
        """verify_token should return True for valid tokens."""
        with patch("drishti.auth.jwt_utils.get_settings", return_value=mock_settings):
            token = create_access_token(test_user)
            is_valid = verify_token(token)

        assert is_valid is True

    def test_verify_token_invalid(self, mock_settings: MagicMock) -> None:
        """verify_token should return False for invalid tokens."""
        with patch("drishti.auth.jwt_utils.get_settings", return_value=mock_settings):
            is_valid = verify_token("invalid.token.here")

        assert is_valid is False

    def test_decode_expired_token(
        self,
        mock_settings: MagicMock,
        test_user: AuthUser,
    ) -> None:
        """decode_token should return None for expired tokens."""
        with patch("drishti.auth.jwt_utils.get_settings", return_value=mock_settings):
            token = create_access_token(
                test_user,
                expires_delta=timedelta(seconds=-1),
            )
            payload = decode_token(token)

        assert payload is None

    def test_refresh_token_round_trip(self, mock_settings: MagicMock) -> None:
        """Refresh token creation and decoding should work."""
        with patch("drishti.auth.jwt_utils.get_settings", return_value=mock_settings):
            token = create_refresh_token("user123")
            user_id = decode_refresh_token(token)

        assert user_id == "user123"


class TestOIDCProviders:
    """Test OIDC authentication providers."""

    def test_google_provider_authorization_url(self) -> None:
        """GoogleOIDCProvider should build correct auth URL."""
        provider = GoogleOIDCProvider(
            client_id="test-client-id",
            client_secret="test-secret",
        )
        url = provider.get_authorization_url(
            redirect_uri="http://localhost:3000/callback",
            state="csrf-state",
        )
        assert "accounts.google.com" in url
        assert "test-client-id" in url
        assert "csrf-state" in url

    def test_github_provider_authorization_url(self) -> None:
        """GitHubOIDCProvider should build correct auth URL."""
        provider = GitHubOIDCProvider(
            client_id="test-client-id",
            client_secret="test-secret",
        )
        url = provider.get_authorization_url(
            redirect_uri="http://localhost:3000/callback",
            state="csrf-state",
        )
        assert "github.com" in url
        assert "test-client-id" in url
        assert "csrf-state" in url

    def test_google_provider_properties(self) -> None:
        """GoogleOIDCProvider should have correct properties."""
        provider = GoogleOIDCProvider(
            client_id="test",
            client_secret="secret",
        )
        assert provider.name == "google"
        assert "accounts.google.com" in provider.authorize_url

    def test_github_provider_properties(self) -> None:
        """GitHubOIDCProvider should have correct properties."""
        provider = GitHubOIDCProvider(
            client_id="test",
            client_secret="secret",
        )
        assert provider.name == "github"
        assert "github.com" in provider.authorize_url

    def test_get_enabled_providers_none(self) -> None:
        """get_enabled_providers should return empty list if none configured."""
        mock_settings = MagicMock()
        mock_settings.google_client_id = ""
        mock_settings.google_client_secret = ""
        mock_settings.github_client_id = ""
        mock_settings.github_client_secret = ""

        with patch("drishti.auth.oidc.get_settings", return_value=mock_settings):
            providers = get_enabled_providers()

        assert providers == []

    def test_get_enabled_providers_google_only(self) -> None:
        """get_enabled_providers should return only configured providers."""
        mock_settings = MagicMock()
        mock_settings.google_client_id = "google-id"
        mock_settings.google_client_secret = "google-secret"
        mock_settings.github_client_id = ""
        mock_settings.github_client_secret = ""

        with patch("drishti.auth.oidc.get_settings", return_value=mock_settings):
            providers = get_enabled_providers()

        assert providers == ["google"]

    def test_get_enabled_providers_both(self) -> None:
        """get_enabled_providers should return all configured providers."""
        mock_settings = MagicMock()
        mock_settings.google_client_id = "google-id"
        mock_settings.google_client_secret = "google-secret"
        mock_settings.github_client_id = "github-id"
        mock_settings.github_client_secret = "github-secret"

        with patch("drishti.auth.oidc.get_settings", return_value=mock_settings):
            providers = get_enabled_providers()

        assert "google" in providers
        assert "github" in providers
