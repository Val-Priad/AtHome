from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StoredObject:
    object_key: str
    last_modified: datetime


@dataclass(frozen=True, slots=True)
class DeleteObjectsResult:
    deleted_keys: tuple[str, ...]
    failed_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StoredObjectInspection:
    content_type: str
    size_bytes: int
    header_bytes: bytes


class ObjectStorageError(RuntimeError):
    """Raised when an object storage operation cannot be completed."""


class ObjectStorageProtocol(Protocol):
    def create_upload_url(
        self,
        *,
        object_key: str,
        content_type: str,
        size_bytes: int,
    ) -> str: ...

    def inspect_object(
        self,
        object_key: str,
    ) -> StoredObjectInspection | None: ...

    def promote_object(
        self,
        *,
        source_key: str,
        destination_key: str,
    ) -> bool: ...

    def iter_objects(self, *, prefix: str) -> Iterable[StoredObject]: ...

    def delete_objects(
        self, object_keys: list[str]
    ) -> DeleteObjectsResult: ...
