from uuid import UUID

from sqlalchemy.orm import Session

from application.ports.transaction_manager import TransactionManagerProtocol
from domain.estate.estate_media_repository import EstateMediaRepository
from domain.estate.estate_participants_service import EstateParticipantsService
from domain.estate.estate_service import EstateService
from domain.media.media_enums import MediaPurpose
from domain.media.media_service import MediaService
from domain.media.media_upload_repository import MediaUploadRepository
from domain.user.services.authorization import AuthorizationService
from domain.user.user_model import UserRole
from schemas.estate_schemas.requests.estate_create_request import (
    EstateCreateRequest,
)
from schemas.estate_schemas.requests.estate_create_type import (
    EstateMutationType,
)
from schemas.estate_schemas.responses.estate_create_response import (
    EstateIDResponse,
)


class CreateEstateUseCase:
    def __init__(
        self,
        transactions: TransactionManagerProtocol,
        estate_service: EstateService,
        media_service: MediaService,
        estate_media_repository: EstateMediaRepository,
        media_upload_repository: MediaUploadRepository,
        authorization_service: AuthorizationService,
        participants_service: EstateParticipantsService,
    ) -> None:
        self._transactions = transactions
        self._estate_service = estate_service
        self._media_service = media_service
        self._estate_media_repository = estate_media_repository
        self._media_upload_repository = media_upload_repository
        self._authorization_service = authorization_service
        self._participants_service = participants_service

    def execute(
        self,
        data: EstateCreateRequest,
        requester_id: UUID,
    ) -> EstateIDResponse:
        creation_data = EstateMutationType(**data.model_dump())

        with self._transactions.session() as session:
            self._ensure_rights_and_data_validity(session, requester_id, data)

        vicinities = self._estate_service.get_vicinities_or_empty(
            data.location
        )

        with self._transactions.session() as session:
            self._ensure_rights_and_data_validity(session, requester_id, data)
            self._estate_media_repository.ensure_object_keys_unused(
                session,
                [item.object_key for item in data.media],
            )
            uploads = self._media_upload_repository.lock_for_attachment(
                session,
                object_keys=[item.object_key for item in data.media],
                uploader_id=requester_id,
                purpose=MediaPurpose.estate,
                media_types_by_key={
                    item.object_key: item.media_type for item in data.media
                },
            )
            self._media_service.finalize_objects(
                uploads=list(uploads.values()),
            )
            estate = self._estate_service.create_estate(
                session, creation_data, vicinities
            )
            self._media_upload_repository.consume(
                session,
                list(uploads.values()),
            )
            return EstateIDResponse(id=estate.id)

    def _ensure_rights_and_data_validity(
        self,
        session: Session,
        requester_id: UUID,
        data: EstateCreateRequest,
    ) -> None:
        self._authorization_service.ensure_has_rights(
            session, requester_id, UserRole.admin
        )
        self._participants_service.check_participants(session, data)
