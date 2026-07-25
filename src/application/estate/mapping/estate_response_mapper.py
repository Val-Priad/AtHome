from collections.abc import Iterable

from application.media.media_url_builder import MediaUrlBuilder
from application.users.mapping.user_response_mapper import UserResponseMapper
from domain.estate.enums.estate_media_enums import MediaType
from domain.estate.estate_model import Estate
from domain.estate.models.estate_media_model import EstateMedia
from schemas.estate_schemas.responses.estate_filter_response import (
    EstateFilterItem,
    EstateFilterResponse,
)
from schemas.estate_schemas.responses.estate_get_response import (
    EstateGeneralGetResponse,
    EstateGetResponseWithSeller,
    EstateUserResponse,
)
from schemas.estate_schemas.responses.estate_media_response import (
    EstateMediaResponse,
)


class EstateResponseMapper:
    def __init__(
        self,
        media_url_builder: MediaUrlBuilder,
        user_response_mapper: UserResponseMapper,
    ) -> None:
        self._media_url_builder = media_url_builder
        self._user_response_mapper = user_response_mapper

    def to_public_estate(self, estate: Estate) -> EstateGeneralGetResponse:
        return EstateGeneralGetResponse.model_validate(
            self._get_estate_data(estate)
        )

    def to_staff_estate(self, estate: Estate) -> EstateGetResponseWithSeller:
        data = self._get_estate_data(estate)
        data.update(
            seller=self._to_user(estate.seller),
            seller_id=estate.seller_id,
        )
        return EstateGetResponseWithSeller.model_validate(data)

    def to_filter_response(
        self,
        estates: Iterable[Estate],
        *,
        total: int,
        page: int,
        page_size: int,
    ) -> EstateFilterResponse:
        return EstateFilterResponse(
            items=[self._to_filter_item(estate) for estate in estates],
            total=total,
            page=page,
            page_size=page_size,
        )

    def to_media(self, media: EstateMedia) -> EstateMediaResponse:
        return EstateMediaResponse(
            id=media.id,
            object_key=media.object_key,
            media_type=media.media_type,
            alt=media.alt,
            position=media.position,
            url=self._media_url_builder.build(media.object_key),
        )

    def _get_estate_data(self, estate: Estate) -> dict[str, object]:
        return {
            "id": estate.id,
            "agent_id": estate.agent_id,
            "estate_type": estate.estate_type,
            "offer_type": estate.offer_type,
            "created_at": estate.created_at,
            "updated_at": estate.updated_at,
            "agent": self._to_user(estate.agent),
            "location": estate.location,
            "pricing": estate.pricing,
            "listing": estate.listing,
            "utilities": estate.utilities,
            "details": estate.details,
            "apartment": estate.apartment,
            "house": estate.house,
            "translations": estate.translations,
            "media": [self.to_media(media) for media in estate.media],
            "vicinities": estate.vicinities,
        }

    def _to_user(self, user: object | None) -> EstateUserResponse | None:
        if user is None:
            return None
        return self._user_response_mapper.to_response(EstateUserResponse, user)

    def _to_filter_item(self, estate: Estate) -> EstateFilterItem:
        preview = self._get_preview(estate.media)

        return EstateFilterItem(
            id=estate.id,
            estate_type=estate.estate_type,
            apartment_layout=(
                estate.apartment.apartment_layout
                if estate.apartment is not None
                else None
            ),
            room_count=(
                estate.house.room_count if estate.house is not None else None
            ),
            house_type=(
                estate.house.house_type if estate.house is not None else None
            ),
            usable_area=estate.details.usable_area,
            preview=self.to_media(preview) if preview is not None else None,
            price=estate.pricing.price,
            price_unit=estate.pricing.price_unit,
        )

    @staticmethod
    def _get_preview(media: list[EstateMedia]) -> EstateMedia | None:
        return next(
            (item for item in media if item.media_type == MediaType.image),
            None,
        )
