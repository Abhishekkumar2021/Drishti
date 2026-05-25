"""Path helpers for document ingestion routing."""

from __future__ import annotations

from pathlib import Path

_OPENAPI_EXACT_NAMES = frozenset(
    {
        "openapi.yaml",
        "openapi.yml",
        "openapi.json",
        "swagger.yaml",
        "swagger.yml",
        "swagger.json",
    },
)


def is_openapi_spec_path(file_path: str) -> bool:
    """Return whether a path looks like a root OpenAPI/Swagger specification file."""
    name = Path(file_path).name.lower()
    if name in _OPENAPI_EXACT_NAMES:
        return True
    return name.startswith("openapi.") and name.endswith((".yaml", ".yml", ".json"))
