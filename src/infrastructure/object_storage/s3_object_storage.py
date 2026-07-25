from collections.abc import Iterator
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from application.ports.object_storage import (
    DeleteObjectsResult,
    ObjectStorageError,
    StoredObject,
    StoredObjectInspection,
)

_NOT_FOUND_ERROR_CODES = frozenset({"404", "NoSuchKey", "NotFound"})
_MAX_DELETE_OBJECTS = 1000


class S3ObjectStorage:
    def __init__(
        self,
        *,
        bucket_name: str,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        presigned_url_ttl_seconds: int = 300,
        client: Any | None = None,
    ) -> None:
        if presigned_url_ttl_seconds <= 0:
            raise ValueError("Presigned URL TTL must be greater than zero")

        self._bucket_name = bucket_name
        self._presigned_url_ttl_seconds = presigned_url_ttl_seconds
        self._client = (
            client
            if client is not None
            else boto3.client(
                "s3",
                config=Config(signature_version="s3v4"),
                **{
                    key: value
                    for key, value in {
                        "region_name": region,
                        "aws_access_key_id": access_key_id,
                        "aws_secret_access_key": secret_access_key,
                    }.items()
                    if value is not None
                },
            )
        )

    def create_upload_url(
        self,
        *,
        object_key: str,
        content_type: str,
        size_bytes: int,
    ) -> str:
        try:
            return self._client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self._bucket_name,
                    "Key": object_key,
                    "ContentType": content_type,
                    "ContentLength": size_bytes,
                },
                ExpiresIn=self._presigned_url_ttl_seconds,
                HttpMethod="PUT",
            )
        except (BotoCoreError, ClientError) as error:
            raise ObjectStorageError(
                "Failed to create an S3 upload URL"
            ) from error

    def inspect_object(
        self,
        object_key: str,
    ) -> StoredObjectInspection | None:
        try:
            response = self._client.get_object(
                Bucket=self._bucket_name,
                Key=object_key,
                Range="bytes=0-15",
            )
        except ClientError as error:
            error_code = str(error.response.get("Error", {}).get("Code", ""))
            status_code = error.response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode"
            )
            if error_code in _NOT_FOUND_ERROR_CODES or status_code == 404:
                return None
            raise ObjectStorageError("Failed to check an S3 object") from error
        except BotoCoreError as error:
            raise ObjectStorageError("Failed to check an S3 object") from error

        body = response["Body"]
        try:
            try:
                header_bytes = body.read()
            except BotoCoreError as error:
                raise ObjectStorageError(
                    "Failed to read an S3 object"
                ) from error
        finally:
            body.close()

        return StoredObjectInspection(
            content_type=response.get("ContentType", ""),
            size_bytes=self._get_total_size(response),
            header_bytes=header_bytes,
        )

    def promote_object(
        self,
        *,
        source_key: str,
        destination_key: str,
    ) -> bool:
        try:
            self._client.copy_object(
                Bucket=self._bucket_name,
                CopySource={
                    "Bucket": self._bucket_name,
                    "Key": source_key,
                },
                Key=destination_key,
                MetadataDirective="COPY",
            )
        except ClientError as error:
            error_code = str(error.response.get("Error", {}).get("Code", ""))
            status_code = error.response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode"
            )
            if error_code in _NOT_FOUND_ERROR_CODES or status_code == 404:
                return False
            raise ObjectStorageError(
                "Failed to promote an S3 object"
            ) from error
        except BotoCoreError as error:
            raise ObjectStorageError(
                "Failed to promote an S3 object"
            ) from error
        return True

    @staticmethod
    def _get_total_size(response: dict[str, Any]) -> int:
        content_range = response.get("ContentRange")
        if content_range:
            return int(content_range.rsplit("/", maxsplit=1)[1])
        return int(response["ContentLength"])

    def iter_objects(self, *, prefix: str) -> Iterator[StoredObject]:
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=self._bucket_name,
                Prefix=prefix,
            )
            for page in pages:
                for item in page.get("Contents", []):
                    yield StoredObject(
                        object_key=item["Key"],
                        last_modified=item["LastModified"],
                    )
        except (BotoCoreError, ClientError) as error:
            raise ObjectStorageError("Failed to list S3 objects") from error

    def delete_objects(self, object_keys: list[str]) -> DeleteObjectsResult:
        deleted_keys: list[str] = []
        failed_keys: list[str] = []
        for offset in range(0, len(object_keys), _MAX_DELETE_OBJECTS):
            batch = object_keys[offset : offset + _MAX_DELETE_OBJECTS]
            result = self._delete_objects_batch(batch)
            deleted_keys.extend(result.deleted_keys)
            failed_keys.extend(result.failed_keys)
        return DeleteObjectsResult(
            deleted_keys=tuple(deleted_keys),
            failed_keys=tuple(failed_keys),
        )

    def _delete_objects_batch(
        self,
        object_keys: list[str],
    ) -> DeleteObjectsResult:
        if not object_keys:
            return DeleteObjectsResult((), ())

        try:
            response = self._client.delete_objects(
                Bucket=self._bucket_name,
                Delete={
                    "Objects": [
                        {"Key": object_key} for object_key in object_keys
                    ],
                    "Quiet": True,
                },
            )
        except (BotoCoreError, ClientError):
            return DeleteObjectsResult((), tuple(object_keys))

        failed_keys = tuple(
            error["Key"]
            for error in response.get("Errors", [])
            if "Key" in error
        )
        failed_key_set = set(failed_keys)
        return DeleteObjectsResult(
            deleted_keys=tuple(
                key for key in object_keys if key not in failed_key_set
            ),
            failed_keys=failed_keys,
        )
