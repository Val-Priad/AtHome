from uuid import UUID

from sqlalchemy.orm import Session

from application.ports.transaction_manager import TransactionManagerProtocol
from domain.estate.estate_media_repository import EstateMediaRepository
from domain.estate.estate_participants_service import EstateParticipantsService
from domain.estate.estate_repository import EstateRepository
from domain.estate.estate_service import EstateService
from domain.media.media_enums import MediaPurpose
from domain.media.media_service import MediaService
from domain.media.media_upload_repository import MediaUploadRepository
from domain.user.services.authorization import AuthorizationService
from domain.user.user_model import UserRole
from exceptions.custom_exceptions.estate_exceptions import EstateNotFoundError
from exceptions.custom_exceptions.media_exceptions import (
    InvalidMediaObjectKeyError,
)
from schemas.estate_schemas.requests.estate_update_request import (
    EstateUpdateRequest,
)
from schemas.estate_schemas.responses.estate_create_response import (
    EstateIDResponse,
)


class UpdateEstateUseCase:
    def __init__(
        self,
        transactions: TransactionManagerProtocol,
        estate_service: EstateService,
        authorization_service: AuthorizationService,
        participants_service: EstateParticipantsService,
        media_service: MediaService,
        estate_media_repository: EstateMediaRepository,
        estate_repository: EstateRepository,
        media_upload_repository: MediaUploadRepository,
    ) -> None:
        self._transactions = transactions
        self._estate_service = estate_service
        self._authorization_service = authorization_service
        self._participants_service = participants_service
        self._media_service = media_service
        self._estate_media_repository = estate_media_repository
        self._estate_repository = estate_repository
        self._media_upload_repository = media_upload_repository

    def execute(
        self,
        estate_id: UUID,
        data: EstateUpdateRequest,
        requester_id: UUID,
    ) -> EstateIDResponse:
        with self._transactions.session() as session:
            self._ensure_rights_and_data_validity(
                session,
                requester_id,
                data,
            )
            if not self._estate_repository.estate_exists(session, estate_id):
                raise EstateNotFoundError()

        vicinities = self._estate_service.get_vicinities_or_empty(
            data.location
        )

        with self._transactions.session() as session:
            self._ensure_rights_and_data_validity(
                session,
                requester_id,
                data,
            )
            estate = self._estate_repository.get_full_estate_by_id_for_update(
                session,
                estate_id,
            )
            current_media_types = {
                item.object_key: item.media_type for item in estate.media
            }
            for item in data.media:
                current_media_type = current_media_types.get(item.object_key)
                if (
                    current_media_type is not None
                    and item.media_type != current_media_type
                ):
                    raise InvalidMediaObjectKeyError(
                        "Media type cannot be changed for an existing object"
                    )

            added_media = [
                item
                for item in data.media
                if item.object_key not in current_media_types
            ]
            self._estate_media_repository.ensure_object_keys_unused(
                session,
                [item.object_key for item in added_media],
            )
            uploads = self._media_upload_repository.lock_for_attachment(
                session,
                object_keys=[item.object_key for item in added_media],
                uploader_id=requester_id,
                purpose=MediaPurpose.estate,
                media_types_by_key={
                    item.object_key: item.media_type for item in added_media
                },
            )
            self._media_service.finalize_objects(
                uploads=list(uploads.values()),
            )
            estate = self._estate_service.update_estate(
                session=session,
                estate=estate,
                data=data,
                vicinities=vicinities,
            )
            self._media_upload_repository.consume(
                session,
                list(uploads.values()),
            )
            return EstateIDResponse.from_model(estate)

    def _ensure_rights_and_data_validity(
        self,
        session: Session,
        requester_id: UUID,
        data: EstateUpdateRequest,
    ) -> None:
        self._authorization_service.ensure_has_rights(
            session,
            requester_id,
            UserRole.admin,
        )
        self._participants_service.check_participants(session, data)
