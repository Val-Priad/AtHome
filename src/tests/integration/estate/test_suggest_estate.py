from datetime import date, timedelta
from decimal import Decimal

import pytest

from domain.estate.enums.estate_enums import EstateType, OfferType
from domain.estate.enums.estate_listing_enums import ListingStatus
from domain.estate.enums.estate_vicinity_enums import VicinityType
from domain.user.user_model import UserRole
from tests.integration.admin_estate.test_create_estate import (
    get_created_estate,
    set_media_uploader,
)
from tests.integration.conftest import ESTATE_PATH


def base_suggestion_payload():
    future_date = date.today() + timedelta(days=1)

    return {
        "estate_type": EstateType.apartment.value,
        "offer_type": OfferType.sale.value,
        "listing": {
            "available_from": future_date.isoformat(),
        },
        "location": {
            "region": "kyiv_city",
            "city": "Kyiv",
            "street": "Step",
            "house_number": "12A",
            "latitude": 52.2297,
            "longitude": 21.0122,
        },
        "pricing": {
            "price": "123456.78",
            "price_unit": "per_property",
        },
        "details": {
            "usable_area": 48.5,
        },
        "apartment": {
            "apartment_layout": "two_plus_one",
        },
        "translations": [
            {
                "lang_code": "en",
                "title": "Test apartment",
                "description": "Test apartment description",
            }
        ],
        "media": [
            {
                "object_key": "estate-media/image.webp",
                "media_type": "image",
            }
        ],
    }


@pytest.mark.parametrize(
    "logged_in_user",
    [UserRole.user, UserRole.admin, UserRole.agent],
    indirect=True,
)
def test_user_suggest_estate_success(
    client,
    logged_in_user,
    db_session,
):
    payload = base_suggestion_payload()
    set_media_uploader(payload, logged_in_user.id, db_session)

    response = client.post(
        f"{ESTATE_PATH}/suggestions",
        json=payload,
        headers=logged_in_user.headers,
    )

    assert response.status_code == 201

    estate = get_created_estate(db_session, response)

    assert estate.estate_type == EstateType.apartment
    assert estate.offer_type == OfferType.sale

    assert estate.seller_id == logged_in_user.id
    assert estate.agent_id is None

    assert estate.listing is not None
    assert estate.listing.status == ListingStatus.suggested
    assert estate.listing.published_at is None
    assert estate.listing.available_from == date.fromisoformat(
        payload["listing"]["available_from"]
    )

    assert estate.location is not None
    assert estate.location.city == "Kyiv"
    assert estate.location.street == "Step"
    assert estate.location.house_number == "12A"
    assert estate.location.latitude == pytest.approx(52.2297)
    assert estate.location.longitude == pytest.approx(21.0122)

    assert estate.pricing is not None
    assert estate.pricing.price == Decimal("123456.78")

    assert estate.details is not None
    assert estate.details.usable_area == pytest.approx(48.5)

    assert estate.utilities is not None

    assert estate.apartment is not None
    assert estate.apartment.apartment_layout.value == "two_plus_one"
    assert estate.house is None

    assert len(estate.translations) == 1
    assert estate.translations[0].lang_code == "en"
    assert estate.translations[0].title == "Test apartment"

    assert len(estate.media) == 1
    assert estate.media[0].object_key == payload["media"][0]["object_key"]
    assert estate.media[0].position == 0

    assert len(estate.vicinities) == 2
    assert estate.vicinities[0].type == VicinityType.bus_stop
    assert estate.vicinities[0].name == "Test bus stop"
    assert estate.vicinities[0].distance_m == 157
    assert estate.vicinities[1].type == VicinityType.closest
    assert estate.vicinities[1].name == "Test bus stop"
    assert estate.vicinities[1].distance_m == 157


@pytest.mark.parametrize("logged_in_user", [UserRole.user], indirect=True)
def test_suggest_estate_rejects_listing_status(
    client,
    logged_in_user,
):
    payload = base_suggestion_payload()
    payload["listing_status"] = ListingStatus.active.value

    response = client.post(
        f"{ESTATE_PATH}/suggestions",
        json=payload,
        headers=logged_in_user.headers,
    )

    assert response.status_code == 400

    body = response.get_json()
    assert body["error"]["code"] == "request_validation_error"
    assert any(
        error["field"] == "listing_status"
        for error in body["error"].get("errors", [])
    )


@pytest.mark.parametrize("logged_in_user", [UserRole.user], indirect=True)
def test_suggest_estate_rejects_expires_at(
    client,
    logged_in_user,
):
    payload = base_suggestion_payload()
    payload["expires_at"] = (date.today() + timedelta(days=30)).isoformat()

    response = client.post(
        f"{ESTATE_PATH}/suggestions",
        json=payload,
        headers=logged_in_user.headers,
    )

    assert response.status_code == 400

    body = response.get_json()
    assert body["error"]["code"] == "request_validation_error"
    assert any(
        error["field"] == "expires_at"
        for error in body["error"].get("errors", [])
    )


@pytest.mark.parametrize("logged_in_user", [UserRole.user], indirect=True)
@pytest.mark.parametrize("any_user", [UserRole.agent], indirect=True)
def test_suggest_estate_rejects_agent_id(
    client,
    logged_in_user,
    any_user,
):
    payload = base_suggestion_payload()
    payload["agent_id"] = str(any_user.id)

    response = client.post(
        f"{ESTATE_PATH}/suggestions",
        json=payload,
        headers=logged_in_user.headers,
    )

    assert response.status_code == 400

    body = response.get_json()
    assert body["error"]["code"] == "request_validation_error"
    assert any(
        error["field"] == "agent_id"
        for error in body["error"].get("errors", [])
    )


@pytest.mark.parametrize("logged_in_user", [UserRole.user], indirect=True)
@pytest.mark.parametrize("any_user", [UserRole.user], indirect=True)
def test_suggest_estate_rejects_seller_id(
    client,
    logged_in_user,
    any_user,
):
    payload = base_suggestion_payload()
    payload["seller_id"] = str(any_user.id)

    response = client.post(
        f"{ESTATE_PATH}/suggestions",
        json=payload,
        headers=logged_in_user.headers,
    )

    assert response.status_code == 400

    body = response.get_json()
    assert body["error"]["code"] == "request_validation_error"
    assert any(
        error["field"] == "seller_id"
        for error in body["error"].get("errors", [])
    )


def test_suggest_estate_unauthorized_without_token(client):
    payload = base_suggestion_payload()

    response = client.post(
        f"{ESTATE_PATH}/suggestions",
        json=payload,
    )

    assert response.status_code == 401


@pytest.mark.parametrize("logged_in_user", [UserRole.user], indirect=True)
def test_suggest_estate_validation_error(
    client,
    logged_in_user,
):
    response = client.post(
        f"{ESTATE_PATH}/suggestions",
        json={},
        headers=logged_in_user.headers,
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "request_validation_error"
