from contextlib import contextmanager
from pathlib import Path

from alignn.config import ROOT, Settings
from alignn.errors import DomainError


class LocalObjects:
    def __init__(self, base: Path | None = None):
        self.base = (base or ROOT / ".superpowers" / "uploads").resolve()

    def path(self, key: str) -> Path:
        target = (self.base / key).resolve()
        if not target.is_relative_to(self.base):
            raise DomainError("invalid_object", "Invalid file reference.")
        return target

    @contextmanager
    def open(self, key: str):
        with self.path(key).open("rb") as stream:
            yield stream

    def size(self, key: str):
        return self.path(key).stat().st_size

    def delete(self, key: str):
        self.path(key).unlink(missing_ok=True)

    def put_bytes(self, key: str, data: bytes, content_type: str):
        import os

        path = self.path(key)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open("xb") as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(data)


class S3Objects:
    def __init__(self, settings: Settings):
        if not all(
            (settings.object_endpoint, settings.object_access_key, settings.object_secret_key)
        ):
            raise DomainError("storage_unavailable", "Private file storage is not configured.", 503)
        import boto3
        from botocore.config import Config

        self.bucket = settings.object_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.object_endpoint,
            aws_access_key_id=settings.object_access_key,
            aws_secret_access_key=settings.object_secret_key,
            config=Config(
                connect_timeout=10,
                read_timeout=10,
                retries={"max_attempts": 2},
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )

    def upload_url(self, key: str, size: int):
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentLength": size},
            ExpiresIn=300,
        )

    def download_url(self, key: str, filename: str):
        from urllib.parse import quote

        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ResponseContentDisposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            },
            ExpiresIn=300,
        )

    @contextmanager
    def open(self, key: str):
        body = self.client.get_object(Bucket=self.bucket, Key=key)["Body"]
        try:
            yield body
        finally:
            body.close()

    def size(self, key: str):
        from botocore.exceptions import ClientError

        try:
            return self.client.head_object(Bucket=self.bucket, Key=key)["ContentLength"]
        except ClientError as exc:
            if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                raise FileNotFoundError(key) from exc
            raise

    def delete(self, key: str):
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def put_bytes(self, key: str, data: bytes, content_type: str):
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)


def configured_objects(settings: Settings):
    if settings.object_driver == "local" and settings.environment != "production":
        return LocalObjects()
    return S3Objects(settings)
