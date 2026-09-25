"""MinIO/S3 object storage: bucket bootstrap + presigned URLs."""

import functools
from datetime import timedelta
from urllib.parse import urlparse

from minio import Minio

from app.core.config import get_settings

settings = get_settings()


def _client() -> Minio:
    host = urlparse(settings.s3_endpoint).netloc or settings.s3_endpoint
    return Minio(
        host,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=settings.s3_secure,
        region=settings.s3_region,
    )


def ensure_bucket() -> None:
    client = _client()
    if not client.bucket_exists(settings.s3_bucket):
        client.make_bucket(settings.s3_bucket)


async def presigned_get(object_key: str, expiry_seconds: int = 3600) -> str:
    client = _client()
    return client.presigned_get_object(
        settings.s3_bucket, object_key, expires=timedelta(seconds=expiry_seconds)
    )


async def presigned_put(object_key: str, expiry_seconds: int = 900) -> str:
    ensure = functools.partial(_client().bucket_exists, settings.s3_bucket)
    if not ensure():
        _client().make_bucket(settings.s3_bucket)
    return _client().presigned_put_object(
        settings.s3_bucket, object_key, expires=timedelta(seconds=expiry_seconds)
    )


async def object_exists(object_key: str) -> bool:
    try:
        _client().stat_object(settings.s3_bucket, object_key)
        return True
    except Exception:
        return False


def plate_key(tenant_id: str, event_id: str) -> str:
    return f"tenants/{tenant_id}/access-events/{event_id}/plate.jpg"


def overview_key(tenant_id: str, event_id: str) -> str:
    return f"tenants/{tenant_id}/access-events/{event_id}/overview.jpg"


def import_key(tenant_id: str, job_id: str, filename: str) -> str:
    safe = filename.replace("/", "_")
    return f"tenants/{tenant_id}/imports/{job_id}/{safe}"
