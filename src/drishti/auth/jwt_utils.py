"""JWT token creation and verification (US-16.01)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pydantic import ValidationError

from drishti.auth.models import AuthUser, TokenPayload
from drishti.config import get_settings

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"


def create_access_token(
    user: AuthUser,
    *,
    expires_delta: timedelta | None = None,
    secret_key: str | None = None,
) -> str:
    """Create a JWT access token for an authenticated user.

    Args:
        user: The authenticated user.
        expires_delta: Optional custom expiration time.
        secret_key: Optional secret key (uses settings if not provided).

    Returns:
        Encoded JWT token string.
    """
    settings = get_settings()
    key = secret_key or settings.jwt_secret_key

    if not key:
        msg = "JWT_SECRET_KEY is not configured"
        raise ValueError(msg)

    now = datetime.now(UTC)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    exp_time = now + expires_delta

    payload_dict = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "exp": int(exp_time.timestamp()),
        "iat": int(now.timestamp()),
        "iss": "drishti",
        "aud": "drishti-api",
        "provider": user.provider,
    }

    return jwt.encode(payload_dict, key, algorithm=_ALGORITHM)


def decode_token(
    token: str,
    *,
    secret_key: str | None = None,
    verify_exp: bool = True,
) -> TokenPayload | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string.
        secret_key: Optional secret key (uses settings if not provided).
        verify_exp: Whether to verify token expiration.

    Returns:
        Decoded token payload, or None if invalid.
    """
    settings = get_settings()
    key = secret_key or settings.jwt_secret_key

    if not key:
        logger.error("JWT_SECRET_KEY is not configured")
        return None

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[_ALGORITHM],
            options={
                "verify_exp": verify_exp,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
        payload["exp"] = datetime.fromtimestamp(payload["exp"], tz=UTC)
        payload["iat"] = datetime.fromtimestamp(payload["iat"], tz=UTC)
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        logger.debug("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug("Invalid token: %s", e)
        return None
    except ValidationError as e:
        logger.debug("Token payload validation failed: %s", e)
        return None


def verify_token(token: str, *, secret_key: str | None = None) -> bool:
    """Check if a token is valid without decoding the full payload.

    Args:
        token: The JWT token string.
        secret_key: Optional secret key.

    Returns:
        True if token is valid, False otherwise.
    """
    return decode_token(token, secret_key=secret_key) is not None


def create_refresh_token(
    user_id: str,
    *,
    expires_delta: timedelta | None = None,
    secret_key: str | None = None,
) -> str:
    """Create a refresh token for session renewal.

    Args:
        user_id: The user ID.
        expires_delta: Optional custom expiration time.
        secret_key: Optional secret key.

    Returns:
        Encoded refresh token.
    """
    settings = get_settings()
    key = secret_key or settings.jwt_secret_key

    if not key:
        msg = "JWT_SECRET_KEY is not configured"
        raise ValueError(msg)

    now = datetime.now(UTC)
    if expires_delta is None:
        expires_delta = timedelta(days=7)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "exp": (now + expires_delta).timestamp(),
        "iat": now.timestamp(),
    }

    return jwt.encode(payload, key, algorithm=_ALGORITHM)


def decode_refresh_token(
    token: str,
    *,
    secret_key: str | None = None,
) -> str | None:
    """Decode a refresh token and return the user ID.

    Args:
        token: The refresh token string.
        secret_key: Optional secret key.

    Returns:
        User ID if valid, None otherwise.
    """
    settings = get_settings()
    key = secret_key or settings.jwt_secret_key

    if not key:
        return None

    try:
        payload = jwt.decode(token, key, algorithms=[_ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return str(payload.get("sub"))
    except jwt.InvalidTokenError:
        return None
