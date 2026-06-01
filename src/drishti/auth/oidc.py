"""OIDC authentication providers (US-16.01).

Supports Google and GitHub OAuth2/OIDC for user authentication.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from drishti.auth.models import AuthUser
from drishti.config import get_settings

logger = logging.getLogger(__name__)


class OIDCProvider(ABC):
    """Base class for OIDC authentication providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (google, github)."""

    @property
    @abstractmethod
    def authorize_url(self) -> str:
        """OAuth2 authorization endpoint URL."""

    @abstractmethod
    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        *,
        scope: str | None = None,
    ) -> str:
        """Build the authorization URL for user login.

        Args:
            redirect_uri: Callback URL after authentication.
            state: CSRF protection state parameter.
            scope: Optional OAuth2 scopes.

        Returns:
            Full authorization URL.
        """

    @abstractmethod
    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback.
            redirect_uri: Must match the original redirect_uri.

        Returns:
            Token response containing access_token.
        """

    @abstractmethod
    async def get_user_info(self, access_token: str) -> AuthUser:
        """Fetch user profile from the provider.

        Args:
            access_token: OAuth2 access token.

        Returns:
            Authenticated user profile.
        """


class GoogleOIDCProvider(OIDCProvider):
    """Google OIDC authentication provider."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    @property
    def name(self) -> str:
        return "google"

    @property
    def authorize_url(self) -> str:
        return "https://accounts.google.com/o/oauth2/v2/auth"

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        *,
        scope: str | None = None,
    ) -> str:
        default_scope = "openid email profile"
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope or default_scope,
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.authorize_url}?{httpx.QueryParams(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    async def get_user_info(self, access_token: str) -> AuthUser:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

        return AuthUser(
            id=f"google:{data['id']}",
            email=data["email"],
            name=data.get("name"),
            picture=data.get("picture"),
            provider="google",
            provider_id=data["id"],
            email_verified=data.get("verified_email", False),
        )


class GitHubOIDCProvider(OIDCProvider):
    """GitHub OAuth2 authentication provider."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    @property
    def name(self) -> str:
        return "github"

    @property
    def authorize_url(self) -> str:
        return "https://github.com/login/oauth/authorize"

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        *,
        scope: str | None = None,
    ) -> str:
        default_scope = "read:user user:email"
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "scope": scope or default_scope,
            "state": state,
        }
        return f"{self.authorize_url}?{httpx.QueryParams(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    async def get_user_info(self, access_token: str) -> AuthUser:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            response.raise_for_status()
            user_data = response.json()

            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            email_response.raise_for_status()
            emails = email_response.json()

        primary_email = next(
            (e["email"] for e in emails if e.get("primary")),
            emails[0]["email"] if emails else None,
        )
        email_verified = any(e.get("verified") and e.get("primary") for e in emails)

        return AuthUser(
            id=f"github:{user_data['id']}",
            email=primary_email or f"{user_data['login']}@users.noreply.github.com",
            name=user_data.get("name") or user_data["login"],
            picture=user_data.get("avatar_url"),
            provider="github",
            provider_id=str(user_data["id"]),
            email_verified=email_verified,
        )


def create_oidc_provider(provider_name: str) -> OIDCProvider:
    """Create an OIDC provider instance from configuration.

    Args:
        provider_name: Provider name ("google" or "github").

    Returns:
        Configured OIDC provider instance.

    Raises:
        ValueError: If provider is not configured or unknown.
    """
    settings = get_settings()

    if provider_name == "google":
        if not settings.google_client_id or not settings.google_client_secret:
            msg = "Google OAuth not configured (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)"
            raise ValueError(msg)
        return GoogleOIDCProvider(
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )

    if provider_name == "github":
        if not settings.github_client_id or not settings.github_client_secret:
            msg = "GitHub OAuth not configured (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)"
            raise ValueError(msg)
        return GitHubOIDCProvider(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
        )

    msg = f"Unknown OIDC provider: {provider_name}"
    raise ValueError(msg)


def get_enabled_providers() -> list[str]:
    """Return list of configured OIDC providers.

    Returns:
        List of provider names that are fully configured.
    """
    settings = get_settings()
    providers = []

    if settings.google_client_id and settings.google_client_secret:
        providers.append("google")

    if settings.github_client_id and settings.github_client_secret:
        providers.append("github")

    return providers
