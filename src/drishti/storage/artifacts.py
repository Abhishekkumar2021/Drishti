"""MinIO-backed artifact storage."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from drishti.config import Settings

logger = logging.getLogger(__name__)


class ArtifactStorage:
    """Store and retrieve workspace uploads in MinIO."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Minio | None = None
        if settings.minio_enabled:
            self._client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
                region=settings.minio_region or None,
            )

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def ensure_bucket(self) -> None:
        """Create the artifacts bucket if it does not exist."""
        if self._client is None:
            return
        bucket = self._settings.minio_bucket
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)
            logger.info("Created MinIO bucket %s", bucket)

    def object_key(self, workspace_id: str, filename: str) -> str:
        """S3 object key for a workspace artifact."""
        safe = Path(filename).name
        return f"workspaces/{workspace_id}/artifacts/{safe}"

    def put_bytes(
        self,
        workspace_id: str,
        filename: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes and return the object key."""
        if self._client is None:
            msg = "MinIO is not configured"
            raise RuntimeError(msg)
        key = self.object_key(workspace_id, filename)
        self._client.put_object(
            self._settings.minio_bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return key

    def get_bytes(self, object_key: str) -> bytes:
        """Download object bytes by key."""
        if self._client is None:
            msg = "MinIO is not configured"
            raise RuntimeError(msg)
        response = self._client.get_object(self._settings.minio_bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def ping(self) -> bool:
        """Return True if MinIO is reachable."""
        if self._client is None:
            return False
        try:
            self._client.list_buckets()
            return True
        except S3Error:
            logger.warning("MinIO health check failed", exc_info=True)
            return False
