from uuid import UUID

from application.ports.transaction_manager import TransactionManagerProtocol
from application.users.mapping.user_response_mapper import UserResponseMapper
from domain.media.media_enums import MediaPurpose, MediaType
from domain.media.media_service import MediaService
from domain.media.media_upload_model import MediaUpload
from domain.media.media_upload_repository import MediaUploadRepository
from domain.user.services.me_service import MeService
from schemas.me_schemas.me_requests import UpdateUserPersonalDataRequest
from schemas.me_schemas.me_responses import MeResponse


class UpdatePersonalDataUseCase:
    def __init__(
        self,
        transactions: TransactionManagerProtocol,
        me_service: MeService,
        media_service: MediaService,
        response_mapper: UserResponseMapper,
        media_upload_repository: MediaUploadRepository,
    ) -> None:
        self._transactions = transactions
        self._me_service = me_service
        self._media_service = media_service
        self._response_mapper = response_mapper
        self._media_upload_repository = media_upload_repository

    def execute(
        self, user_id: UUID, data: UpdateUserPersonalDataRequest
    ) -> MeResponse:
        updates = data.model_dump(exclude_unset=True)
        avatar_key = updates.get("avatar_key")

        with self._transactions.session() as session:
            user = self._me_service.get_user_for_update(
                session,
                user_id,
            )
            uploads: dict[str, MediaUpload] = {}
            if avatar_key is not None and avatar_key != user.avatar_key:
                uploads = self._media_upload_repository.lock_for_attachment(
                    session,
                    object_keys=[avatar_key],
                    uploader_id=user_id,
                    purpose=MediaPurpose.user_avatar,
                    media_types_by_key={avatar_key: MediaType.image},
                )
                self._media_service.finalize_objects(
                    uploads=list(uploads.values()),
                )
            user = self._me_service.update_personal_data(
                session, user_id, updates
            )
            if uploads:
                self._media_upload_repository.consume(
                    session,
                    list(uploads.values()),
                )
            return self._response_mapper.to_response(MeResponse, user)
