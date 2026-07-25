from collections.abc import Callable
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from application.ports.object_storage import (
    ObjectStorageError,
    ObjectStorageProtocol,
)
from application.ports.transaction_manager import TransactionManagerProtocol
from domain.media.media_config import (
    MEDIA_CONFIG_BY_PURPOSE,
    MEDIA_FORMAT_BY_CONTENT_TYPE,
)
from domain.media.media_upload_repository import MediaUploadRepository
from exceptions.custom_exceptions.media_exceptions import MediaUploadError
from schemas.media_schemas.requests.media_upload_url_request import (
    MediaUploadUrlRequest,
)
from schemas.media_schemas.responses.presigned_upload_response import (
    PresignedUploadResponse,
    PresignedUploadsResponse,
)


class CreateMediaUploadUrlsUseCase:
    def __init__(
        self,
        *,
        transactions: TransactionManagerProtocol,
        media_upload_repository: MediaUploadRepository,
        object_storage: ObjectStorageProtocol,
        presigned_url_ttl_seconds: int,
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._transactions = transactions
        self._media_upload_repository = media_upload_repository
        self._object_storage = object_storage
        self._presigned_url_ttl_seconds = presigned_url_ttl_seconds
        self._uuid_factory = uuid_factory

    def execute(
        self,
        files: list[MediaUploadUrlRequest],
        requester_id: UUID,
    ) -> PresignedUploadsResponse:
        uploads: list[PresignedUploadResponse] = []
        with self._transactions.session() as session:
            for data in files:
                uploads.append(
                    self._create_upload(
                        session=session,
                        data=data,
                        requester_id=requester_id,
                    )
                )
        return PresignedUploadsResponse(uploads=uploads)

    def _create_upload(
        self,
        *,
        session: Session,
        data: MediaUploadUrlRequest,
        requester_id: UUID,
    ) -> PresignedUploadResponse:
        prefix = MEDIA_CONFIG_BY_PURPOSE[data.purpose].prefix
        media_format = MEDIA_FORMAT_BY_CONTENT_TYPE[data.content_type]
        media_id = self._uuid_factory()
        object_key = (
            f"{prefix}/{requester_id}/{media_id}.{media_format.extension}"
        )
        upload_object_key = (
            f"{prefix}/{requester_id}/pending/"
            f"{media_id}.{media_format.extension}"
        )
        self._media_upload_repository.add(
            session,
            object_key=object_key,
            upload_object_key=upload_object_key,
            uploader_id=requester_id,
            purpose=data.purpose,
            media_type=media_format.media_type,
        )
        try:
            upload_url = self._object_storage.create_upload_url(
                object_key=upload_object_key,
                content_type=data.content_type.value,
                size_bytes=data.size_bytes,
            )
        except ObjectStorageError as error:
            raise MediaUploadError() from error

        return PresignedUploadResponse(
            upload_url=upload_url,
            object_key=object_key,
            expires_in=self._presigned_url_ttl_seconds,
        )
