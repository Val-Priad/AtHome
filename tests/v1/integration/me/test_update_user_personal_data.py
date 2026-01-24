from conftest import API_PREFIX

from tests.v1.integration.me.me_endpoint import ENDPOINT_PATH


def test_update_user_personal_data_valid(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ENDPOINT_PATH}/update-personal-data",
        json={
            "name": None,
            "avatar_key": None,
            "phone_number": None,
            "description": None,
        },
        headers=logged_in_user["headers"],
    )
    assert response.status_code == 200
    body = response.get_json()
    data = body["data"]
    assert data["name"] is None
    assert data["avatar_key"] is None
    assert data["phone_number"] is None
    assert data["description"] is None


def test_update_user_personal_data_partially_valid(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ENDPOINT_PATH}/update-personal-data",
        json={
            "avatar_key": None,
            "phone_number": None,
            "description": None,
        },
        headers=logged_in_user["headers"],
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
        f"{API_PREFIX}{ENDPOINT_PATH}/update-personal-data",
        json={
            "phone_number": None,
            "description": None,
        },
        headers=logged_in_user["headers"],
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
        f"{API_PREFIX}{ENDPOINT_PATH}/update-personal-data",
        json={"name": "Val Priad           "},
        headers=logged_in_user["headers"],
    )
    assert response.status_code == 200
    body = response.get_json()
    data = body["data"]
    assert data["name"] == "Val Priad"


def test_update_user_personal_data_with_no_data(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ENDPOINT_PATH}/update-personal-data",
        json={},
        headers=logged_in_user["headers"],
    )
    assert response.status_code == 400


def test_update_user_personal_data_with_invalid_phone(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ENDPOINT_PATH}/update-personal-data",
        json={"phone_number": "invalid_phone"},
        headers=logged_in_user["headers"],
    )
    assert response.status_code == 400


def test_update_user_personal_data_email(client, logged_in_user):
    response = client.patch(
        f"{API_PREFIX}{ENDPOINT_PATH}/update-personal-data",
        json={"email": "hacker@gmail.com"},
        headers=logged_in_user["headers"],
    )
    assert response.status_code == 400
