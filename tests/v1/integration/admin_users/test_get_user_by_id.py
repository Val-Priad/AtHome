import pytest
from conftest import ADMIN_USERS_PATH, API_PREFIX

from domain.user.user_model import UserRole
from schemas.admin_schemas.admin_users_schemas.admin_users_responses import (
    UserResponse,
)


@pytest.mark.parametrize("logged_in_user", [UserRole.admin], indirect=True)
def test_get_user_by_id_valid(client, logged_in_user, any_user, db_session):
    csrf = client.get_cookie("csrf_access_token").value
    response = client.get(
        f"{API_PREFIX}{ADMIN_USERS_PATH}/{any_user.id}",
        headers={"X-CSRF-TOKEN": csrf},
    )
    assert response.status_code == 200

    body = response.get_json()
    data = body["data"]

    user_dto = UserResponse.from_model(any_user)
    user_json = user_dto.model_dump(mode="json")

    assert data == user_json
