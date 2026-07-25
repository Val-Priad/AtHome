from collections.abc import Iterator
from uuid import UUID

import pytest

from application.ports.object_storage import (
    DeleteObjectsResult,
    StoredObject,
    StoredObjectInspection,
)
from domain.media.media_enums import MediaPurpose, MediaType
from domain.media.media_service import MediaService
from domain.media.media_upload_model import MediaUpload
from exceptions.custom_exceptions.media_exceptions import (
    InvalidMediaObjectKeyError,
    MediaObjectNotFoundError,
)

UPLOADER_ID = UUID("10000000-0000-0000-0000-000000000001")
MEDIA_ID = UUID("30000000-0000-0000-0000-000000000abc")
IMAGE_KEY = f"estate-media/{UPLOADER_ID}/{MEDIA_ID}.webp"


class FakeStorage:
    def __init__(
        self,
        inspection: StoredObjectInspection | None,
    ) -> None:
        self.inspection = inspection
        self.inspected_keys: list[str] = []
        self.promoted_keys: list[tuple[str, str]] = []

    def inspect_object(
        self,
        object_key: str,
    ) -> StoredObjectInspection | None:
        self.inspected_keys.append(object_key)
        return self.inspection

    def create_upload_url(
        self,
        *,
        object_key: str,
        content_type: str,
        size_bytes: int,
    ) -> str:
        raise NotImplementedError

    def promote_object(
        self,
        *,
        source_key: str,
        destination_key: str,
    ) -> bool:
        if self.inspection is None:
            return False
        self.promoted_keys.append((source_key, destination_key))
        return True

    def iter_objects(self, *, prefix: str) -> Iterator[StoredObject]:
        return iter(())

    def delete_objects(self, object_keys: list[str]) -> DeleteObjectsResult:
        raise NotImplementedError


def _valid_webp() -> StoredObjectInspection:
    return StoredObjectInspection(
        content_type="image/webp",
        size_bytes=1024,
        header_bytes=b"RIFF\x00\x00\x00\x00WEBP",
    )


def test_rejects_missing_object() -> None:
    storage = FakeStorage(None)
    with pytest.raises(MediaObjectNotFoundError):
        _finalize(storage)

    assert storage.promoted_keys == []


def test_rejects_file_whose_bytes_do_not_match_declared_type() -> None:
    disguised_file = StoredObjectInspection(
        content_type="image/webp",
        size_bytes=1024,
        header_bytes=b"<script>alert(1)</script>",
    )

    with pytest.raises(InvalidMediaObjectKeyError):
        _finalize(FakeStorage(disguised_file))


def test_finalizes_to_a_key_the_upload_url_cannot_overwrite() -> None:
    storage = FakeStorage(_valid_webp())

    _finalize(storage)

    assert storage.inspected_keys == [IMAGE_KEY]
    assert storage.promoted_keys == [(_upload_key(), IMAGE_KEY)]


def _upload_key() -> str:
    return f"estate-media/{UPLOADER_ID}/pending/{MEDIA_ID}.webp"


def _finalize(
    storage: FakeStorage,
) -> None:
    upload = MediaUpload(
        object_key=IMAGE_KEY,
        upload_object_key=_upload_key(),
        uploader_id=UPLOADER_ID,
        purpose=MediaPurpose.estate,
        media_type=MediaType.image,
    )
    MediaService(storage).finalize_objects(
        uploads=[upload],
    )
