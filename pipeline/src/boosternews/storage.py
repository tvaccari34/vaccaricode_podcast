"""S3-compatible object storage helper (works with MinIO and any S3 provider).

Task 1.6: provision the audio bucket and provide a thin client other modules reuse to upload
narration / episode files and build public URLs for the podcast feed.
"""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from .config import get_settings


def get_client():
    """Return a configured boto3 S3 client pointed at the configured endpoint."""
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        aws_access_key_id=s.s3_access_key_id,
        aws_secret_access_key=s.s3_secret_access_key,
        region_name=s.s3_region,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket(bucket: str | None = None) -> str:
    """Create the audio bucket if needed and make it public-read. Returns the bucket name.

    Episode audio is meant to be publicly served (podcast feed enclosures / the site player), so
    the bucket gets a public GetObject policy. In production you would typically front this with a
    CDN; the public-read policy is still the right default for podcast media.
    """
    s = get_settings()
    bucket = bucket or s.s3_bucket_audio
    client = get_client()
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)
    _set_public_read(client, bucket)
    return bucket


def _set_public_read(client, bucket: str) -> None:
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            }
        ],
    }
    try:
        client.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
    except ClientError:
        pass  # best-effort; some managed providers manage policies separately


def upload_file(local_path: str | Path, key: str, *, content_type: str | None = None) -> str:
    """Upload a local file under ``key`` and return its key."""
    s = get_settings()
    local_path = Path(local_path)
    content_type = (
        content_type or mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
    )
    client = get_client()
    client.upload_file(
        str(local_path),
        s.s3_bucket_audio,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def upload_bytes(data: bytes, key: str, *, content_type: str = "application/octet-stream") -> str:
    """Upload raw bytes under ``key`` and return its key."""
    s = get_settings()
    client = get_client()
    client.put_object(Bucket=s.s3_bucket_audio, Key=key, Body=data, ContentType=content_type)
    return key


def delete_object(key: str) -> None:
    """Delete an object by key; ignore if it does not exist (idempotent cleanup)."""
    s = get_settings()
    try:
        get_client().delete_object(Bucket=s.s3_bucket_audio, Key=key)
    except ClientError:
        pass


def public_url(key: str) -> str:
    """Build the public URL for an object key (used in the podcast feed enclosure)."""
    s = get_settings()
    if s.s3_public_base_url:
        return f"{s.s3_public_base_url.rstrip('/')}/{key.lstrip('/')}"
    return f"{s.s3_endpoint_url.rstrip('/')}/{s.s3_bucket_audio}/{key.lstrip('/')}"


def presigned_url(key: str, *, expires: int = 3600) -> str:
    """Return a temporary presigned GET URL for private objects."""
    s = get_settings()
    return get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": s.s3_bucket_audio, "Key": key},
        ExpiresIn=expires,
    )
