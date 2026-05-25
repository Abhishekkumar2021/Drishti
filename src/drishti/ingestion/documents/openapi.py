"""OpenAPI / Swagger spec parser (US-04.05)."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from drishti.api.schemas import UniversalChunk
from drishti.ingestion.base import BaseParser
from drishti.ingestion.documents.paths import is_openapi_spec_path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


class OpenApiParser(BaseParser):
    """Parses OpenAPI 3.x and Swagger 2.x specs into per-endpoint chunks."""

    def parse(
        self,
        file_content: bytes,
        file_path: str,
        *,
        last_modified: datetime | None = None,
    ) -> list[UniversalChunk]:
        if not is_openapi_spec_path(file_path):
            return []

        spec = _load_spec(file_content, file_path)
        if spec is None or not _is_openapi_document(spec):
            return []

        source_id = hashlib.sha256(file_content).hexdigest()
        indexed_at = last_modified if last_modified is not None else datetime.now(UTC)
        paths = spec.get("paths")
        if not isinstance(paths, dict):
            return []

        chunks: list[UniversalChunk] = []
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, operation in path_item.items():
                if method.startswith("x-") or not isinstance(operation, dict):
                    continue
                if method.lower() not in _HTTP_METHODS:
                    continue
                content = _format_operation(path, method.upper(), operation, spec)
                operation_id = operation.get("operationId")
                name = str(operation_id) if operation_id else f"{method.upper()} {path}"
                chunks.append(
                    UniversalChunk(
                        id=str(uuid.uuid4()),
                        source_id=source_id,
                        content=content,
                        content_type="api_endpoint",
                        file_path=file_path,
                        source_type="openapi",
                        language="openapi",
                        name=name,
                        context_path=f"{method.upper()} {path}",
                        last_modified=indexed_at,
                    ),
                )
        return chunks


_HTTP_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "trace"},
)


def _load_spec(file_content: bytes, file_path: str) -> dict[str, Any] | None:
    text = file_content.decode("utf-8", errors="replace")
    if file_path.lower().endswith(".json"):
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            return None
        return loaded if isinstance(loaded, dict) else None
    if yaml is None:
        return None
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _is_openapi_document(spec: dict[str, Any]) -> bool:
    return "openapi" in spec or "swagger" in spec


def _format_operation(
    path: str,
    method: str,
    operation: dict[str, Any],
    spec: dict[str, Any],
) -> str:
    lines = [f"# {method} {path}"]
    summary = operation.get("summary") or operation.get("description")
    if summary:
        lines.append(str(summary).strip())

    parameters = operation.get("parameters", [])
    if isinstance(parameters, list) and parameters:
        lines.append("\n## Parameters")
        for param in parameters:
            if not isinstance(param, dict):
                continue
            name = param.get("name", "param")
            location = param.get("in", "")
            required = param.get("required", False)
            schema = param.get("schema", {})
            param_type = schema.get("type", "") if isinstance(schema, dict) else ""
            lines.append(
                f"- `{name}` ({location}, type={param_type}, required={required})",
            )

    request_body = operation.get("requestBody")
    if isinstance(request_body, dict):
        lines.append("\n## Request body")
        lines.append(_describe_request_body(request_body, spec))

    responses = operation.get("responses")
    if isinstance(responses, dict) and responses:
        lines.append("\n## Responses")
        for status, response in responses.items():
            if not isinstance(response, dict):
                continue
            description = response.get("description", "")
            lines.append(f"- **{status}**: {description}")

    return "\n".join(lines).strip()


def _describe_request_body(request_body: dict[str, Any], spec: dict[str, Any]) -> str:
    content = request_body.get("content")
    if not isinstance(content, dict):
        return request_body.get("description", "") or "present"
    parts: list[str] = []
    for media_type, media in content.items():
        if not isinstance(media, dict):
            continue
        schema = media.get("schema")
        parts.append(f"- `{media_type}`: {_schema_summary(schema, spec)}")
    return "\n".join(parts) if parts else "present"


def _schema_summary(schema: Any, spec: dict[str, Any]) -> str:
    if not isinstance(schema, dict):
        return "schema"
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        return ref
    return str(schema.get("type", "object"))
