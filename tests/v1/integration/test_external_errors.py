from tests.v1.integration.conftest import (
    ADMIN_USERS_PATH,
    API_PREFIX,
    AUTH_ENDPOINT_PATH,
)


# HTTP
def test_login_invalid_type_of_content(client):
    response = client.post(
        f"{API_PREFIX}{AUTH_ENDPOINT_PATH}/login",
        data="email=user@example.com&password=45245",
        content_type="text/plain",
    )
    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "unsupported_media_type"


# JWT
def test_get_user_by_id_not_logged_in(client, any_user):
    response = client.get(
        f"{API_PREFIX}{ADMIN_USERS_PATH}/{any_user.id}",
    )
    assert response.get_json()["error"]["code"] == "no_authorization"
    assert response.status_code == 401
