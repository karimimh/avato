from __future__ import annotations

import hashlib
from typing import Any, BinaryIO, cast

import boto3
from botocore.client import BaseClient

from app.core.config import settings
from app.storage.base import ObjectInfo


class S3ObjectStorage:
    def __init__(
        self,
        client: BaseClient | None = None,
        public_client: BaseClient | None = None,
    ) -> None:
        self.client = client or cast(
            BaseClient,
            boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                region_name=settings.s3_region,
                aws_access_key_id=settings.s3_access_key_id,
                aws_secret_access_key=settings.s3_secret_access_key,
                use_ssl=settings.s3_use_ssl,
            ),
        )
        self.public_client = public_client or (
            self.client
            if client is not None or settings.s3_public_endpoint_url == settings.s3_endpoint_url
            else cast(
                BaseClient,
                boto3.client(
                    "s3",
                    endpoint_url=settings.s3_public_endpoint_url,
                    region_name=settings.s3_region,
                    aws_access_key_id=settings.s3_access_key_id,
                    aws_secret_access_key=settings.s3_secret_access_key,
                    use_ssl=settings.s3_use_ssl,
                ),
            )
        )
        self.bucket = settings.s3_bucket

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except self.client.exceptions.ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def put_private(self, key: str, body: BinaryIO, content_type: str) -> ObjectInfo:
        digest = hashlib.sha256()
        payload = body.read()
        digest.update(payload)
        arguments: dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": payload,
            "ContentType": content_type,
        }
        if settings.s3_server_side_encryption:
            arguments["ServerSideEncryption"] = settings.s3_server_side_encryption
        self.client.put_object(**arguments)
        return ObjectInfo(key, len(payload), content_type, digest.hexdigest())

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def delete_prefix(self, prefix: str) -> int:
        deleted = 0
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            objects = [{"Key": item["Key"]} for item in page.get("Contents", [])]
            if objects:
                self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects})
                deleted += len(objects)
        return deleted

    def read(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return bytes(response["Body"].read())

    def presigned_get(self, key: str, expires_seconds: int = 300) -> str:
        return str(
            self.public_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=max(30, min(expires_seconds, 900)),
            )
        )
