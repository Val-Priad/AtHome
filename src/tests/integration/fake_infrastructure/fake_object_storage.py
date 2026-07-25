from collections.abc import Iterator

from application.ports.object_storage import (
    DeleteObjectsResult,
    ObjectStorageError,
    StoredObject,
    StoredObjectInspection,
)
from domain.media.media_config import MEDIA_FORMAT_BY_EXTENSION


class FakeObjectStorage:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.existing_object_keys: set[str] | None = None
        self.checked_object_keys: list[str] = []
        self.promoted_object_keys: list[tuple[str, str]] = []
        self.inspection_error: ObjectStorageError | None = None
        self.deleted_object_keys: list[str] = []
        self.delete_error: Exception | None = None
        self.failed_delete_keys: set[str] = set()
        self.stored_objects: list[StoredObject] = []

    def create_upload_url(
        self,
        *,
        object_key: str,
        content_type: str,
        size_bytes: int,
    ) -> str:
        return f"https://storage.test/{object_key}"

    def inspect_object(
        self,
        object_key: str,
    ) -> StoredObjectInspection | None:
        self.checked_object_keys.append(object_key)
        if self.inspection_error is not None:
            raise self.inspection_error
        if (
            self.existing_object_keys is not None
            and object_key not in self.existing_object_keys
        ):
            return None

        extension = object_key.rsplit(".", maxsplit=1)[-1]
        signatures = {
            "jpg": b"\xff\xd8\xff",
            "png": b"\x89PNG\r\n\x1a\n",
            "webp": b"RIFF\x00\x00\x00\x00WEBP",
            "mp4": b"\x00\x00\x00\x18ftypisom",
        }
        content_type, _ = MEDIA_FORMAT_BY_EXTENSION[extension]
        return StoredObjectInspection(
            content_type=content_type.value,
            size_bytes=1024,
            header_bytes=signatures[extension],
        )

    def promote_object(
        self,
        *,
        source_key: str,
        destination_key: str,
    ) -> bool:
        if self.existing_object_keys is not None:
            if source_key not in self.existing_object_keys:
                return False
            self.existing_object_keys.add(destination_key)
        self.promoted_object_keys.append((source_key, destination_key))
        return True

    def iter_objects(self, *, prefix: str) -> Iterator[StoredObject]:
        yield from (
            stored_object
            for stored_object in self.stored_objects
            if stored_object.object_key.startswith(prefix)
        )

    def delete_objects(self, object_keys: list[str]) -> DeleteObjectsResult:
        if self.delete_error is not None:
            raise self.delete_error

        deleted = [
            key for key in object_keys if key not in self.failed_delete_keys
        ]
        failed = [key for key in object_keys if key in self.failed_delete_keys]
        self.deleted_object_keys.extend(deleted)
        return DeleteObjectsResult(tuple(deleted), tuple(failed))
