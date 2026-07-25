from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import Mock
from uuid import UUID

import pytest

from application.media.create_media_upload_urls_use_case import (
    CreateMediaUploadUrlsUseCase,
)
from application.ports.object_storage import ObjectStorageError
from domain.media.media_config import (
    MAX_IMAGE_SIZE_BYTES,
    MAX_VIDEO_SIZE_BYTES,
)
from exceptions.custom_exceptions.media_exceptions import (
    InvalidMediaObjectKeyError,
    MediaObjectAlreadyUsedError,
    MediaObjectNotFoundError,
    MediaUploadError,
)
from exceptions.custom_exceptions.validation_exceptions import (
    RequestValidationError,
)
from exceptions.error_catalog import (
    get_description_for_exception,
    register_errors,
)
from schemas.media_schemas.requests.media_upload_url_request import (
    MediaUploadUrlRequest,
)

REQUESTER_ID = UUID("10000000-0000-0000-0000-000000000001")
MEDIA_ID = UUID("20000000-0000-0000-0000-000000000002")


def _payload(**overrides):
    payload = {
        "purpose": "estate",
        "content_type": "image/webp",
        "size_bytes": 1024,
    }
    payload.update(overrides)
    return payload


def test_rejects_unsupported_content_type() -> None:
    with pytest.raises(RequestValidationError):
        MediaUploadUrlRequest.from_request(
            _payload(content_type="application/pdf")
        )


def test_rejects_obsolete_filename_field() -> None:
    with pytest.raises(RequestValidationError):
        MediaUploadUrlRequest.from_request(_payload(filename="ignored.webp"))


def test_rejects_oversized_image() -> None:
    with pytest.raises(RequestValidationError):
        MediaUploadUrlRequest.from_request(
            _payload(size_bytes=MAX_IMAGE_SIZE_BYTES + 1)
        )


def test_rejects_oversized_video() -> None:
    with pytest.raises(RequestValidationError):
        MediaUploadUrlRequest.from_request(
            _payload(
                content_type="video/mp4",
                size_bytes=MAX_VIDEO_SIZE_BYTES + 1,
            )
        )


def test_generated_object_key_uses_expected_prefix_and_extension() -> None:
    object_storage = Mock()
    object_storage.create_upload_url.return_value = "https://upload.test/url"
    use_case = _use_case(
        object_storage=object_storage,
        uuid_factory=lambda: MEDIA_ID,
    )
    request = MediaUploadUrlRequest.from_request(
        _payload(
            purpose="user_avatar",
            content_type="image/jpeg",
        )
    )

    response = use_case.execute([request], REQUESTER_ID).uploads[0]

    expected_key = f"user-avatars/{REQUESTER_ID}/{MEDIA_ID}.jpg"
    expected_upload_key = f"user-avatars/{REQUESTER_ID}/pending/{MEDIA_ID}.jpg"
    assert response.object_key == expected_key
    object_storage.create_upload_url.assert_called_once_with(
        object_key=expected_upload_key,
        content_type="image/jpeg",
        size_bytes=1024,
    )


def test_wraps_object_storage_error_as_media_upload_error() -> None:
    object_storage = Mock()
    storage_error = ObjectStorageError("S3 unavailable")
    object_storage.create_upload_url.side_effect = storage_error
    use_case = _use_case(
        object_storage=object_storage,
    )
    request = MediaUploadUrlRequest.from_request(_payload())

    with pytest.raises(MediaUploadError) as raised:
        use_case.execute([request], REQUESTER_ID)

    assert raised.value.__cause__ is storage_error


def _use_case(
    *,
    object_storage: Mock,
    uuid_factory=lambda: MEDIA_ID,
) -> CreateMediaUploadUrlsUseCase:
    transactions = Mock()

    @contextmanager
    def session() -> Iterator[Mock]:
        yield Mock()

    transactions.session.side_effect = session
    return CreateMediaUploadUrlsUseCase(
        transactions=transactions,
        media_upload_repository=Mock(),
        object_storage=object_storage,
        presigned_url_ttl_seconds=300,
        uuid_factory=uuid_factory,
    )


@pytest.mark.parametrize(
    ("error", "expected_code", "expected_status"),
    [
        (MediaUploadError(), "media_upload_failed", 503),
        (MediaObjectNotFoundError(), "media_object_not_found", 400),
        (InvalidMediaObjectKeyError(), "invalid_media_object_key", 400),
        (MediaObjectAlreadyUsedError(), "media_object_already_used", 409),
    ],
)
def test_media_errors_are_registered(
    error: Exception,
    expected_code: str,
    expected_status: int,
) -> None:
    register_errors()

    description = get_description_for_exception(error)

    assert description.code == expected_code
    assert description.status == expected_status
