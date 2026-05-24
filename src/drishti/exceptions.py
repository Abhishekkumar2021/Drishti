"""Application-specific exceptions and error codes."""

from __future__ import annotations


class DrishtiError(Exception):
    """Base exception for all Drishti application errors."""

    def __init__(self, message: str, *, code: str = "DRISHTI_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ConfigurationError(DrishtiError):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFIGURATION_ERROR")


class AuthenticationError(DrishtiError):
    """Raised when API authentication fails."""

    def __init__(self, message: str = "Invalid or missing API token") -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(DrishtiError):
    """Raised when the caller lacks permission for an operation."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR")


class PathValidationError(DrishtiError):
    """Raised when a filesystem path fails security validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="PATH_VALIDATION_ERROR")


class GitRepositoryError(DrishtiError):
    """Raised when git operations fail or the path is not a repository."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="GIT_REPOSITORY_ERROR")


class ServiceUnavailableError(DrishtiError):
    """Raised when a required downstream service is unavailable."""

    def __init__(self, message: str, *, service: str) -> None:
        super().__init__(message, code="SERVICE_UNAVAILABLE")
        self.service = service
