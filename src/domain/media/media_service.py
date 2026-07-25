from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import PurePosixPath

from application.ports.object_storage import (
    ObjectStorageError,
    ObjectStorageProtocol,
)
from domain.media.media_config import (
    MEDIA_FORMAT_BY_EXTENSION,
)
from domain.media.media_upload_model import MediaUpload
from exceptions.custom_exceptions.media_exceptions import (
    InvalidMediaObjectKeyError,
    MediaObjectNotFoundError,
    MediaUploadError,
)


class MediaService:
    _MAX_FINALIZATION_WORKERS = 5

    def __init__(self, object_storage: ObjectStorageProtocol) -> None:
        self._object_storage = object_storage

    def finalize_objects(
        self,
        *,
        uploads: Sequence[MediaUpload],
    ) -> None:
        if not uploads:
            return

        if len(uploads) == 1:
            self._promote_and_validate(upload=uploads[0])
            return

        with ThreadPoolExecutor(
            max_workers=min(self._MAX_FINALIZATION_WORKERS, len(uploads))
        ) as executor:
            futures = [
                executor.submit(
                    self._promote_and_validate,
                    upload=upload,
                )
                for upload in uploads
            ]
            for future in futures:
                future.result()

    def _promote_and_validate(
        self,
        *,
        upload: MediaUpload,
    ) -> None:
        try:
            promoted = self._object_storage.promote_object(
                source_key=upload.upload_object_key,
                destination_key=upload.object_key,
            )
        except ObjectStorageError as error:
            raise MediaUploadError() from error
        if not promoted:
            raise MediaObjectNotFoundError()
        self._ensure_object_is_valid(
            object_key=upload.object_key,
        )

    def _ensure_object_is_valid(
        self,
        *,
        object_key: str,
    ) -> None:
        try:
            inspection = self._object_storage.inspect_object(object_key)
        except ObjectStorageError as error:
            raise MediaUploadError() from error

        if inspection is None:
            raise MediaObjectNotFoundError()

        extension = PurePosixPath(object_key).suffix.removeprefix(".")
        content_type, media_format = MEDIA_FORMAT_BY_EXTENSION[extension]
        if (
            inspection.content_type != content_type.value
            or inspection.size_bytes <= 0
            or inspection.size_bytes > media_format.max_size_bytes
            or not self._matches_file_signature(
                extension,
                inspection.header_bytes,
            )
        ):
            raise InvalidMediaObjectKeyError(
                "Uploaded media content does not match its declared type"
            )

    @staticmethod
    def _matches_file_signature(extension: str, header: bytes) -> bool:
        if extension == "jpg":
            return header.startswith(b"\xff\xd8\xff")
        if extension == "png":
            return header.startswith(b"\x89PNG\r\n\x1a\n")
        if extension == "webp":
            return (
                len(header) >= 12
                and header.startswith(b"RIFF")
                and header[8:12] == b"WEBP"
            )
        if extension == "mp4":
            return len(header) >= 12 and header[4:8] == b"ftyp"
        return False
