"""Sample module for Python parser tests."""

from dataclasses import dataclass


@dataclass
class AuthService:
    """Authenticates users."""

    def verify(self, token: str) -> bool:
        return bool(token)

    @property
    def is_active(self) -> bool:
        return True


def standalone_helper() -> None:
    """Top-level helper."""
    pass
