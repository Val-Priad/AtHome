from collections.abc import Iterator

from application.ports.object_storage import (
    DeleteObjectsResult,
    StoredObject,
    StoredObjectInspection,
)


class NoOpObjectStorage:
    def create_upload_url(
        self,
        *,
        object_key: str,
        content_type: str,
        size_bytes: int,
    ) -> str:
        return ""

    def inspect_object(
        self,
        object_key: str,
    ) -> StoredObjectInspection | None:
        return None

    def promote_object(
        self,
        *,
        source_key: str,
        destination_key: str,
    ) -> bool:
        return False

    def iter_objects(self, *, prefix: str) -> Iterator[StoredObject]:
        yield from ()

    def delete_objects(self, object_keys: list[str]) -> DeleteObjectsResult:
        return DeleteObjectsResult(tuple(object_keys), ())
