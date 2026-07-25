from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import CursorResult, delete, or_, select, update
from sqlalchemy.orm import Session

from domain.media.media_enums import MediaPurpose, MediaType
from domain.media.media_upload_model import (
    MediaUpload,
    MediaUploadStatus,
)
from exceptions.custom_exceptions.media_exceptions import (
    InvalidMediaObjectKeyError,
    MediaObjectAlreadyUsedError,
)


class MediaUploadRepository:
    def add(
        self,
        session: Session,
        *,
        object_key: str,
        upload_object_key: str,
        uploader_id: UUID,
        purpose: MediaPurpose,
        media_type: MediaType,
    ) -> None:
        session.add(
            MediaUpload(
                object_key=object_key,
                upload_object_key=upload_object_key,
                uploader_id=uploader_id,
                purpose=purpose,
                media_type=media_type,
            )
        )

    def lock_for_attachment(
        self,
        session: Session,
        *,
        object_keys: Sequence[str],
        uploader_id: UUID,
        purpose: MediaPurpose,
        media_types_by_key: Mapping[str, MediaType],
    ) -> dict[str, MediaUpload]:
        if not object_keys:
            return {}

        uploads = {
            upload.object_key: upload
            for upload in session.scalars(
                select(MediaUpload)
                .where(MediaUpload.object_key.in_(object_keys))
                .with_for_update()
            )
        }

        for object_key in object_keys:
            upload = uploads.get(object_key)
            if (
                upload is None
                or upload.uploader_id != uploader_id
                or upload.purpose != purpose
                or upload.media_type != media_types_by_key.get(object_key)
            ):
                raise InvalidMediaObjectKeyError()
            if upload.status != MediaUploadStatus.available:
                raise MediaObjectAlreadyUsedError(
                    "Media object is no longer available for attachment"
                )

        return uploads

    def lock_for_cleanup(
        self,
        session: Session,
        object_keys: Sequence[str],
    ) -> dict[str, MediaUpload]:
        if not object_keys:
            return {}

        uploads = list(
            session.scalars(
                select(MediaUpload)
                .where(
                    or_(
                        MediaUpload.object_key.in_(object_keys),
                        MediaUpload.upload_object_key.in_(object_keys),
                    )
                )
                .with_for_update()
            )
        )
        return {
            key: upload
            for upload in uploads
            for key in (upload.object_key, upload.upload_object_key)
            if key in object_keys
        }

    def delete_expired_available(
        self,
        session: Session,
        cutoff: datetime,
    ) -> int:
        result = cast(
            CursorResult,
            session.execute(
                delete(MediaUpload).where(
                    MediaUpload.status == MediaUploadStatus.available,
                    MediaUpload.created_at < cutoff,
                )
            ),
        )
        return result.rowcount

    def mark_deleting(
        self,
        uploads: Sequence[MediaUpload],
    ) -> None:
        for upload in uploads:
            if upload.status == MediaUploadStatus.available:
                upload.status = MediaUploadStatus.deleting

    def consume(
        self,
        session: Session,
        uploads: Sequence[MediaUpload],
    ) -> None:
        for upload in uploads:
            session.delete(upload)

    def delete_by_object_keys(
        self,
        session: Session,
        object_keys: Sequence[str],
    ) -> None:
        if object_keys:
            session.execute(
                delete(MediaUpload).where(
                    or_(
                        MediaUpload.object_key.in_(object_keys),
                        MediaUpload.upload_object_key.in_(object_keys),
                    )
                )
            )

    def restore_available(
        self,
        session: Session,
        object_keys: Sequence[str],
    ) -> None:
        if object_keys:
            session.execute(
                update(MediaUpload)
                .where(
                    or_(
                        MediaUpload.object_key.in_(object_keys),
                        MediaUpload.upload_object_key.in_(object_keys),
                    ),
                    MediaUpload.status == MediaUploadStatus.deleting,
                )
                .values(status=MediaUploadStatus.available)
            )
