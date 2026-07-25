from datetime import datetime, timezone
from unittest.mock import Mock, call
from urllib.parse import parse_qs, urlsplit

import pytest
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    ResponseStreamingError,
)

from application.ports.object_storage import ObjectStorageError
from infrastructure.object_storage.s3_object_storage import (
    S3ObjectStorage,
)


def _storage(client: Mock, *, ttl: int = 300) -> S3ObjectStorage:
    return S3ObjectStorage(
        bucket_name="test-bucket",
        region="eu-north-1",
        access_key_id="test-access-key",
        secret_access_key="test-secret-key",
        presigned_url_ttl_seconds=ttl,
        client=client,
    )


def _client_error(
    code: str,
    *,
    operation: str = "HeadObject",
    status: int = 400,
) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": "S3 error"},
            "ResponseMetadata": {"HTTPStatusCode": status},
        },
        operation,
    )


def test_create_upload_url() -> None:
    client = Mock()
    client.generate_presigned_url.return_value = "https://upload.test/url"
    storage = _storage(client, ttl=600)

    result = storage.create_upload_url(
        object_key="estate-media/image.webp",
        content_type="image/webp",
        size_bytes=5242880,
    )

    assert result == "https://upload.test/url"
    client.generate_presigned_url.assert_called_once_with(
        "put_object",
        Params={
            "Bucket": "test-bucket",
            "Key": "estate-media/image.webp",
            "ContentType": "image/webp",
            "ContentLength": 5242880,
        },
        ExpiresIn=600,
        HttpMethod="PUT",
    )


def test_upload_url_signature_enforces_declared_content_length() -> None:
    storage = S3ObjectStorage(
        bucket_name="test-bucket",
        region="us-east-1",
        access_key_id="test-access-key",
        secret_access_key="test-secret-key",
    )

    upload_url = storage.create_upload_url(
        object_key="estate-media/image.webp",
        content_type="image/webp",
        size_bytes=5242880,
    )

    query = parse_qs(urlsplit(upload_url).query)
    signed_headers = query.get("X-Amz-SignedHeaders", [""])[0].split(";")

    assert "content-length" in signed_headers


def test_create_upload_url_wraps_sdk_errors() -> None:
    client = Mock()
    error = EndpointConnectionError(endpoint_url="https://s3.test")
    client.generate_presigned_url.side_effect = error

    with pytest.raises(ObjectStorageError) as raised:
        _storage(client).create_upload_url(
            object_key="estate-media/image.webp",
            content_type="image/webp",
            size_bytes=5242880,
        )

    assert raised.value.__cause__ is error


def test_inspect_object_returns_content_metadata_and_signature() -> None:
    client = Mock()
    client.get_object.return_value = {
        "Body": Mock(read=Mock(return_value=b"RIFF\x00\x00\x00\x00WEBP")),
        "ContentType": "image/webp",
        "ContentLength": 16,
        "ContentRange": "bytes 0-15/1024",
    }

    result = _storage(client).inspect_object("estate-media/image.webp")

    assert result is not None
    assert result.content_type == "image/webp"
    assert result.size_bytes == 1024
    assert result.header_bytes.startswith(b"RIFF")
    client.get_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="estate-media/image.webp",
        Range="bytes=0-15",
    )


def test_inspect_object_wraps_stream_read_errors() -> None:
    client = Mock()
    body = Mock()
    error = ResponseStreamingError(error="connection closed")
    body.read.side_effect = error
    client.get_object.return_value = {"Body": body}

    with pytest.raises(ObjectStorageError) as raised:
        _storage(client).inspect_object("estate-media/image.webp")

    assert raised.value.__cause__ is error
    body.close.assert_called_once_with()


@pytest.mark.parametrize("error_code", ["404", "NotFound", "NoSuchKey"])
def test_inspect_object_returns_none_for_missing_object(
    error_code: str,
) -> None:
    client = Mock()
    client.get_object.side_effect = _client_error(error_code, status=404)

    assert _storage(client).inspect_object("missing.webp") is None


@pytest.mark.parametrize(
    ("error_code", "status"),
    [("AccessDenied", 403), ("InternalError", 500)],
)
def test_inspect_object_raises_for_non_not_found_errors(
    error_code: str,
    status: int,
) -> None:
    client = Mock()
    error = _client_error(error_code, status=status)
    client.get_object.side_effect = error

    with pytest.raises(ObjectStorageError) as raised:
        _storage(client).inspect_object("estate-media/image.webp")

    assert raised.value.__cause__ is error


def test_promote_object_copies_to_an_immutable_destination_key() -> None:
    client = Mock()

    promoted = _storage(client).promote_object(
        source_key="estate-media/user/pending/image.webp",
        destination_key="estate-media/user/image.webp",
    )

    assert promoted is True
    client.copy_object.assert_called_once_with(
        Bucket="test-bucket",
        CopySource={
            "Bucket": "test-bucket",
            "Key": "estate-media/user/pending/image.webp",
        },
        Key="estate-media/user/image.webp",
        MetadataDirective="COPY",
    )


def test_promote_object_wraps_sdk_errors() -> None:
    client = Mock()
    error = EndpointConnectionError(endpoint_url="https://s3.test")
    client.copy_object.side_effect = error

    with pytest.raises(ObjectStorageError) as raised:
        _storage(client).promote_object(
            source_key="pending.webp",
            destination_key="final.webp",
        )

    assert raised.value.__cause__ is error


def test_promote_object_reports_missing_source() -> None:
    client = Mock()
    client.copy_object.side_effect = _client_error("NoSuchKey", status=404)

    promoted = _storage(client).promote_object(
        source_key="missing.webp",
        destination_key="final.webp",
    )

    assert promoted is False


def test_iter_objects_maps_across_pages_and_skips_empty_pages() -> None:
    client = Mock()
    paginator = client.get_paginator.return_value
    first_last_modified = datetime(2026, 7, 20, tzinfo=timezone.utc)
    second_last_modified = datetime(2026, 7, 21, tzinfo=timezone.utc)
    paginator.paginate.return_value = [
        {
            "Contents": [
                {
                    "Key": "user-avatars/one.webp",
                    "LastModified": first_last_modified,
                }
            ]
        },
        {},
        {
            "Contents": [
                {
                    "Key": "user-avatars/two.webp",
                    "LastModified": second_last_modified,
                }
            ]
        },
    ]

    result = list(_storage(client).iter_objects(prefix="user-avatars/"))

    assert [(item.object_key, item.last_modified) for item in result] == [
        ("user-avatars/one.webp", first_last_modified),
        ("user-avatars/two.webp", second_last_modified),
    ]
    client.get_paginator.assert_called_once_with("list_objects_v2")
    paginator.paginate.assert_called_once_with(
        Bucket="test-bucket",
        Prefix="user-avatars/",
    )


def test_iter_objects_wraps_sdk_errors() -> None:
    client = Mock()
    error = EndpointConnectionError(endpoint_url="https://s3.test")
    client.get_paginator.side_effect = error

    with pytest.raises(ObjectStorageError) as raised:
        list(_storage(client).iter_objects(prefix="estate-media/"))

    assert raised.value.__cause__ is error


def test_delete_objects_uses_batches_of_at_most_1000() -> None:
    client = Mock()
    client.delete_objects.return_value = {}
    object_keys = [f"estate-media/{index}.webp" for index in range(1001)]

    result = _storage(client).delete_objects(object_keys)

    assert result.deleted_keys == tuple(object_keys)
    assert result.failed_keys == ()
    assert client.delete_objects.call_count == 2
    assert client.delete_objects.call_args_list == [
        call(
            Bucket="test-bucket",
            Delete={
                "Objects": [
                    {"Key": object_key} for object_key in object_keys[:1000]
                ],
                "Quiet": True,
            },
        ),
        call(
            Bucket="test-bucket",
            Delete={
                "Objects": [{"Key": object_keys[1000]}],
                "Quiet": True,
            },
        ),
    ]


def test_delete_objects_reports_partial_errors() -> None:
    client = Mock()
    client.delete_objects.return_value = {
        "Errors": [{"Key": "image.webp", "Code": "AccessDenied"}]
    }

    result = _storage(client).delete_objects(["image.webp", "video.mp4"])

    assert result.deleted_keys == ("video.mp4",)
    assert result.failed_keys == ("image.webp",)


def test_delete_objects_reports_batch_failure_without_losing_later_batches() -> (
    None
):
    client = Mock()
    client.delete_objects.side_effect = [
        EndpointConnectionError(endpoint_url="https://s3.test"),
        {},
    ]
    keys = [f"estate-media/{index}.webp" for index in range(1001)]

    result = _storage(client).delete_objects(keys)

    assert result.failed_keys == tuple(keys[:1000])
    assert result.deleted_keys == (keys[1000],)
