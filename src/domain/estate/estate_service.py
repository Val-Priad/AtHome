from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from application.ports.vicinity_client import VicinityClientProtocol
from domain.estate.enums.estate_enums import EstateType
from domain.estate.enums.estate_listing_enums import ListingStatus
from domain.estate.estate_model import Estate
from domain.estate.estate_repository import EstateRepository
from domain.estate.models.estate_apartment_model import EstateApartment
from domain.estate.models.estate_details_model import EstateDetails
from domain.estate.models.estate_house_model import EstateHouse
from domain.estate.models.estate_listing_model import EstateListing
from domain.estate.models.estate_location_model import EstateLocation
from domain.estate.models.estate_media_model import EstateMedia
from domain.estate.models.estate_pricing_model import EstatePricing
from domain.estate.models.estate_translation_model import EstateTranslation
from domain.estate.models.estate_utilities_model import EstateUtilities
from domain.estate.models.estate_vicinity_model import EstateVicinity
from schemas.estate_schemas.requests.estate_create_type import (
    EstateMutationType,
)
from schemas.estate_schemas.requests.estate_filter_request import (
    EstateAdminFilterRequest,
    EstatePublicFilterRequest,
)
from schemas.estate_schemas.requests.estate_update_request import (
    EstateUpdateRequest,
)
from schemas.estate_schemas.sections.location_section import (
    EstateLocationSection,
)


class EstateService:
    def __init__(
        self,
        estate_repository: EstateRepository,
        vicinity_client: VicinityClientProtocol,
    ):
        self.estate_repository = estate_repository
        self.vicinity_client = vicinity_client

    def create_estate(
        self,
        session: Session,
        data: EstateMutationType,
        vicinities: list[EstateVicinity],
    ) -> Estate:
        estate = Estate(
            seller_id=data.seller_id,
            agent_id=data.agent_id,
            estate_type=data.estate_type,
            offer_type=data.offer_type,
            listing=EstateListing(
                status=data.listing_status,
                published_at=(
                    datetime.now(timezone.utc)
                    if data.listing_status == ListingStatus.active
                    else None
                ),
                available_from=data.listing.available_from,
                expires_at=data.expires_at,
            ),
            location=self._create_related_model(
                EstateLocation,
                data.location,
            ),
            pricing=self._create_related_model(
                EstatePricing,
                data.pricing,
            ),
            details=self._create_related_model(
                EstateDetails,
                data.details,
            ),
            utilities=(
                self._create_related_model(EstateUtilities, data.utilities)
                if data.utilities is not None
                else EstateUtilities()
            ),
            translations=[
                EstateTranslation(**translation.model_dump())
                for translation in data.translations
            ],
            media=self._create_media(data.media),
        )

        if data.apartment is not None:
            estate.apartment = self._create_related_model(
                EstateApartment,
                data.apartment,
            )

        if data.house is not None:
            estate.house = self._create_related_model(
                EstateHouse,
                data.house,
            )

        estate.vicinities = vicinities

        return self.estate_repository.add(session, estate)

    def get_vicinities_or_empty(
        self,
        location: EstateLocationSection,
    ) -> list[EstateVicinity]:
        result = self.vicinity_client.fetch_vicinity(
            location.latitude,
            location.longitude,
        )

        if not result.ok:
            return []

        grouped_places = result.data or {}
        vicinities: list[EstateVicinity] = []

        for vicinity_type, places in grouped_places.items():
            for place in places:
                vicinities.append(
                    EstateVicinity(
                        type=vicinity_type,
                        name=place.name,
                        latitude=place.latitude,
                        longitude=place.longitude,
                        distance_m=place.distance_m,
                    )
                )

        return vicinities

    def get_filtered_estate(
        self,
        session: Session,
        filters: EstatePublicFilterRequest,
        requester_id: UUID | None = None,
    ) -> tuple[list[Estate], int]:
        return self.estate_repository.get_public_estates_by_filters(
            session=session,
            filters=filters,
            requester_id=requester_id,
        )

    def get_admin_filtered_estate(
        self,
        session: Session,
        filters: EstateAdminFilterRequest,
        requester_id: UUID | None = None,
    ) -> tuple[list[Estate], int]:
        return self.estate_repository.get_admin_estates_by_filters(
            session=session,
            filters=filters,
            requester_id=requester_id,
        )

    def update_estate(
        self,
        session: Session,
        estate: Estate,
        data: EstateUpdateRequest,
        vicinities: list[EstateVicinity],
    ) -> Estate:
        old_status = estate.listing.status

        estate.seller_id = data.seller_id
        estate.agent_id = data.agent_id
        estate.estate_type = data.estate_type
        estate.offer_type = data.offer_type

        estate.listing.status = data.listing_status
        estate.listing.available_from = data.listing.available_from
        estate.listing.expires_at = data.expires_at

        if (
            old_status != ListingStatus.active
            and data.listing_status == ListingStatus.active
        ):
            estate.listing.published_at = date.today()

        if data.listing_status == ListingStatus.draft:
            estate.listing.published_at = None

        self._update_related_model(estate.location, data.location)
        self._update_related_model(estate.pricing, data.pricing)
        self._update_related_model(estate.details, data.details)

        if data.utilities is not None:
            self._update_related_model(estate.utilities, data.utilities)
        else:
            estate.utilities = EstateUtilities()

        self._update_property_type_sections(estate, data)
        self._replace_translations(estate, data)
        self._replace_media(session, estate, data)

        estate.vicinities = vicinities

        session.flush()

        return estate

    def _update_property_type_sections(self, estate: Estate, data) -> None:
        if data.estate_type == EstateType.apartment:
            estate.house = None

            if estate.apartment is None:
                estate.apartment = self._create_related_model(
                    EstateApartment,
                    data.apartment,
                )
            else:
                self._update_related_model(estate.apartment, data.apartment)

        if data.estate_type == EstateType.house:
            estate.apartment = None

            if estate.house is None:
                estate.house = self._create_related_model(
                    EstateHouse,
                    data.house,
                )
            else:
                self._update_related_model(estate.house, data.house)

    def _replace_translations(self, estate: Estate, data) -> None:
        estate.translations = [
            EstateTranslation(**translation.model_dump())
            for translation in data.translations
        ]

    def _replace_media(self, session: Session, estate: Estate, data) -> None:
        estate.media = []
        session.flush()
        estate.media = self._create_media(data.media)

    @staticmethod
    def _create_media(media_items) -> list[EstateMedia]:
        return [
            EstateMedia(
                object_key=item.object_key,
                media_type=item.media_type,
                alt=item.alt,
                position=position,
            )
            for position, item in enumerate(media_items)
        ]

    @staticmethod
    def _create_related_model(model_class, data):
        return model_class(**data.model_dump(exclude_none=True))

    @staticmethod
    def _update_related_model(model, data) -> None:
        for key, value in data.model_dump().items():
            setattr(model, key, value)
