import pytest
from conftest import API_PREFIX, ME_ENDPOINT_PATH
from sqlalchemy import select

from domain.user.user_model import User


def test_update_user_personal_data_valid(client, db_session, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/update-personal-data",
        json={
            "name": None,
            "avatar_key": None,
            "phone_number": None,
            "description": None,
        },
        headers=logged_in_user.headers,
    )
    assert response.status_code == 200
    body = response.get_json()
    data = body["data"]
    assert data["name"] is None
    assert data["avatar_key"] is None
    assert data["phone_number"] is None
    assert data["description"] is None

    db_session.expire_all()
    user = db_session.scalar(
        select(User).where(User.email == logged_in_user.email)
    )
    assert user.name is None
    assert user.avatar_key is None
    assert user.phone_number is None
    assert user.description is None


def test_update_user_personal_data_partially_valid(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/update-personal-data",
        json={
            "avatar_key": None,
            "phone_number": None,
            "description": None,
        },
        headers=logged_in_user.headers,
    )
    assert response.status_code == 200
    body = response.get_json()
    data = body["data"]
    assert data["name"] == "Val Priad"
    assert data["avatar_key"] is None
    assert data["phone_number"] is None
    assert data["description"] is None


def test_update_user_personal_data_partially2_valid(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/update-personal-data",
        json={
            "phone_number": None,
            "description": None,
        },
        headers=logged_in_user.headers,
    )
    assert response.status_code == 200
    body = response.get_json()
    data = body["data"]
    assert data["name"] == "Val Priad"
    assert data["avatar_key"] == "avatars/default/user_1.png"
    assert data["phone_number"] is None
    assert data["description"] is None


def test_update_user_personal_data_name_is_trimmed(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/update-personal-data",
        json={"name": "Val Priad           "},
        headers=logged_in_user.headers,
    )
    assert response.status_code == 200
    body = response.get_json()
    data = body["data"]
    assert data["name"] == "Val Priad"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {},
            id="no_data_provided",
        ),
        pytest.param(
            {"phone_number": "invalid_phone"},
            id="invalid_phone_number",
        ),
        pytest.param(
            {"email": "hacker@gmail.com"},
            id="email_update_not_allowed",
        ),
    ],
)
def test_update_user_personal_data_validation(client, logged_in_user, payload):
    response = client.patch(
        f"{API_PREFIX}{ME_ENDPOINT_PATH}/update-personal-data",
        json=payload,
        headers=logged_in_user.headers,
    )

    assert response.status_code == 400
